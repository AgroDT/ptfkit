#!/usr/bin/env python3
# /// script
# requires-python = ">=3.14"
# dependencies = [
#     "httpx2>=2.12,<3",
#     "numpy>=2.0,<3",
#     "rasterio>=1.4,<2",
# ]
# ///

"""Prepare a SoilGrids-based performance benchmark dataset for ptfkit.

The output is a tar.zst archive containing aligned, little-endian float64 NPY 1.0
arrays. Network access, raster decoding, sampling, unit conversion, and compression
happen only here; benchmark harnesses only need to unpack and read NPY files.

This dataset is intended exclusively as a realistic performance workload. It is not
a validation dataset for the scientific applicability or accuracy of any PTF.

Run directly with uv:

    uv run prepare_dataset.py

Example:
    uv run prepare_dataset.py \
        --output benchmarks/data/soilgrids.tar.zst \
        --samples 16777216

"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import tarfile
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Final

import httpx2
import numpy as np
import rasterio


WCS_URL: Final = 'https://maps.isric.org/mapserv'
SOILGRIDS_CRS: Final = 'http://www.opengis.net/def/crs/EPSG/0/152160'

DEPTHS: Final = (
    '0-5cm',
    '5-15cm',
    '15-30cm',
    '30-60cm',
    '60-100cm',
    '100-200cm',
)

# Fixed benchmark crop in the native SoilGrids Interrupted Goode Homolosine CRS.
# This is the Ghana example extent used by the SoilGrids documentation. The region
# itself has no scientific significance for this benchmark.
DEFAULT_BOUNDS: Final = (-337500.0, 527500.0, 152500.0, 1242500.0)

DEFAULT_SAMPLES: Final = 1 << 24
DEFAULT_SEED: Final = 0x5054464B  # "PTFK"


@dataclass(frozen=True)
class Column:
    source: str
    unit: str
    scale: float
    positive: bool = False
    description: str = ''

    def convert(self, values: np.ndarray) -> np.ndarray:
        return np.asarray(values, dtype=np.float64) * self.scale


# Scale factors convert the integer SoilGrids map values directly into units that
# are convenient for ptfkit benchmark inputs.
COLUMNS: Final[dict[str, Column]] = {
    'sand': Column(
        source='sand',
        unit='%',
        scale=1.0 / 10.0,
        positive=True,
        description='Sand content by mass.',
    ),
    'silt': Column(
        source='silt',
        unit='%',
        scale=1.0 / 10.0,
        positive=True,
        description='Silt content by mass.',
    ),
    'clay': Column(
        source='clay',
        unit='%',
        scale=1.0 / 10.0,
        positive=True,
        description='Clay content by mass.',
    ),
    'bulk_density': Column(
        source='bdod',
        unit='g/cm^3',
        scale=1.0 / 100.0,
        positive=True,
        description='Bulk density of the fine earth fraction.',
    ),
    # SoilGrids SOC is stored in dg/kg. Dividing by 100 converts directly to
    # g/100g (%).
    'organic_carbon': Column(
        source='soc',
        unit='%',
        scale=1.0 / 100.0,
        description='Soil organic carbon by mass.',
    ),
    # SoilGrids water-content rasters are stored in 10^-3 cm^3/cm^3.
    'theta_33': Column(
        source='wv0033',
        unit='cm^3/cm^3',
        scale=1.0 / 1000.0,
        description='Volumetric water content at 33 kPa.',
    ),
    'theta_1500': Column(
        source='wv1500',
        unit='cm^3/cm^3',
        scale=1.0 / 1000.0,
        description='Volumetric water content at 1500 kPa.',
    ),
}

DEFAULT_COLUMNS: Final = tuple(COLUMNS)


def parse_args() -> argparse.Namespace:
    def positive_int(value: str) -> int:
        parsed = int(value)
        if parsed > 0:
            return parsed
        msg = f'{value!r} is not a positive integer'
        raise argparse.ArgumentTypeError(msg)

    parser = argparse.ArgumentParser(
        description='Prepare a compressed SoilGrids benchmark corpus for ptfkit.',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        '--output',
        type=Path,
        default=Path('fixtures/soilgrids.tar.zst'),
        help='Output tar.zst archive.',
    )
    parser.add_argument(
        '--cache-dir',
        type=Path,
        default=Path('.cache/ptfkit-soilgrids'),
        help='Cache downloaded WCS GeoTIFF subsets.',
    )
    parser.add_argument(
        '--samples',
        type=positive_int,
        default=DEFAULT_SAMPLES,
        help='Number of aligned samples to write.',
    )
    parser.add_argument(
        '--seed',
        type=positive_int,
        default=DEFAULT_SEED,
        help='Deterministic sampling seed.',
    )
    parser.add_argument(
        '--depths',
        nargs='+',
        choices=DEPTHS,
        default=list(DEPTHS),
        help='SoilGrids depth intervals to sample.',
    )
    parser.add_argument(
        '--columns',
        nargs='+',
        choices=tuple(COLUMNS),
        default=list(DEFAULT_COLUMNS),
        help='Columns to include in the archive.',
    )
    parser.add_argument(
        '--bounds',
        nargs=4,
        type=float,
        metavar=('XMIN', 'YMIN', 'XMAX', 'YMAX'),
        default=DEFAULT_BOUNDS,
        help='Subset bounds in SoilGrids EPSG:152160.',
    )
    parser.add_argument(
        '--zstd-level',
        type=int,
        default=19,
        choices=range(1, 20),
        help='Zstandard compression level.',
    )
    parser.add_argument(
        '--force-download',
        action='store_true',
        help='Ignore cached WCS GeoTIFFs and download them again.',
    )
    return parser.parse_args()


def make_client() -> httpx2.Client:
    return httpx2.Client(
        headers={'User-Agent': 'ptfkit-benchmark-dataset-preparer/1'},
        transport=httpx2.HTTPTransport(retries=5),
    )


def cache_key(bounds: tuple[float, float, float, float]) -> str:
    payload = json.dumps(
        {
            'bounds': bounds,
            'crs': SOILGRIDS_CRS,
            'prediction': 'mean',
        },
        sort_keys=True,
        separators=(',', ':'),
    ).encode()
    return hashlib.sha256(payload).hexdigest()[:16]


def coverage_id(source: str, depth: str) -> str:
    return f'{source}_{depth}_mean'


def download_coverage(
    client: httpx2.Client,
    source: str,
    depth: str,
    bounds: tuple[float, float, float, float],
    destination: Path,
    *,
    force: bool,
) -> None:
    if destination.exists() and not force:
        return

    destination.parent.mkdir(parents=True, exist_ok=True)
    partial = destination.with_suffix(destination.suffix + '.part')
    partial.unlink(missing_ok=True)

    xmin, ymin, xmax, ymax = bounds
    params = (
        ('map', f'/map/{source}.map'),
        ('SERVICE', 'WCS'),
        ('VERSION', '2.0.1'),
        ('REQUEST', 'GetCoverage'),
        ('COVERAGEID', coverage_id(source, depth)),
        ('FORMAT', 'GEOTIFF_INT16'),
        ('SUBSET', f'X({xmin:g},{xmax:g})'),
        ('SUBSET', f'Y({ymin:g},{ymax:g})'),
        ('SUBSETTINGCRS', SOILGRIDS_CRS),
        ('OUTPUTCRS', SOILGRIDS_CRS),
    )

    print(f'Downloading {coverage_id(source, depth)}')
    with client.stream(
        'GET', WCS_URL, params=params, timeout=httpx2.Timeout(30, connect=600)
    ) as response:
        response.raise_for_status()

        content_type = response.headers.get('content-type', '').lower()
        if 'xml' in content_type or content_type.startswith('text/'):
            message = next(response.iter_text(4000)).strip()
            msg = f'SoilGrids WCS returned {content_type!r} instead of GeoTIFF:\n{message}'
            raise SystemExit(msg)

        with partial.open('wb') as file:
            for chunk in response.iter_bytes(chunk_size=1024 * 1024):
                if chunk:
                    file.write(chunk)

    # Open the result before moving it into the cache so a WCS exception document
    # or truncated download cannot poison subsequent runs.
    if err := is_partial_invalid(partial):
        partial.unlink(missing_ok=True)
        raise SystemExit(err)

    partial.replace(destination)


def is_partial_invalid(path: Path) -> str | None:
    with rasterio.open(path) as dataset:
        if dataset.count != 1:
            return f'Expected one raster band in {path}, got {dataset.count}'
        if dataset.width <= 0 or dataset.height <= 0:
            return f'Invalid raster dimensions in {path}'
    return None


def layer_paths(
    cache_dir: Path,
    sources: tuple[str, ...],
    depth: str,
    bounds: tuple[float, float, float, float],
) -> dict[str, Path]:
    root = cache_dir / cache_key(bounds)
    return {source: root / f'{coverage_id(source, depth)}.tif' for source in sources}


def validate_grid(paths: dict[str, Path]) -> tuple[int, int]:
    expected_shape: tuple[int, int] | None = None
    expected_transform = None
    expected_crs = None

    for source, path in paths.items():
        with rasterio.open(path) as dataset:
            shape = (dataset.height, dataset.width)
            if expected_shape is None:
                expected_shape = shape
                expected_transform = dataset.transform
                expected_crs = dataset.crs
                continue

            if shape != expected_shape:
                msg = f'Raster grid mismatch for {source}: {shape} != {expected_shape}'
                raise SystemExit(msg)
            if dataset.transform != expected_transform:
                msg = f'Raster transform mismatch for {source}'
                raise SystemExit(msg)
            if dataset.crs != expected_crs:
                msg = f'Raster CRS mismatch for {source}'
                raise SystemExit(msg)

    if expected_shape is None:
        raise RuntimeError

    return expected_shape


def valid_mask(
    paths: dict[str, Path],
    source_rules: dict[str, bool],
) -> np.ndarray:
    mask: np.ndarray | None = None

    for source, path in paths.items():
        with rasterio.open(path) as dataset:
            values = dataset.read(1, masked=True)
            current = ~np.ma.getmaskarray(values)
            if source_rules[source]:
                current &= np.asarray(values.data) > 0

            if mask is None:
                mask = np.array(current, dtype=np.bool_, copy=True)
            else:
                mask &= current

    if mask is None:
        raise RuntimeError

    return mask


def select_indices(
    mask: np.ndarray,
    count: int,
    rng: np.random.Generator,
) -> np.ndarray:
    valid = np.flatnonzero(mask.reshape(-1))
    if valid.size <= count:
        return valid

    positions = rng.choice(valid.size, size=count, replace=False, shuffle=False)
    return valid[positions]


def open_output_arrays(
    directory: Path,
    columns: tuple[str, ...],
    samples: int,
) -> dict[str, np.memmap]:
    arrays: dict[str, np.memmap] = {}
    for name in columns:
        arrays[name] = np.lib.format.open_memmap(
            directory / f'{name}.npy',
            mode='w+',
            dtype=np.dtype('<f8'),
            shape=(samples,),
            fortran_order=False,
            version=(1, 0),
        )
    return arrays


def fill_slice(
    outputs: dict[str, np.memmap],
    columns: tuple[str, ...],
    paths: dict[str, Path],
    selected: np.ndarray,
    start: int,
) -> int:
    stop = start + selected.size

    by_source: dict[str, list[str]] = {}
    for name in columns:
        by_source.setdefault(COLUMNS[name].source, []).append(name)

    for source, names in by_source.items():
        with rasterio.open(paths[source]) as dataset:
            raw = dataset.read(1).reshape(-1)[selected]

        for name in names:
            outputs[name][start:stop] = COLUMNS[name].convert(raw)

    return stop


def prepare_arrays(
    *,
    directory: Path,
    cache_dir: Path,
    columns: tuple[str, ...],
    depths: tuple[str, ...],
    bounds: tuple[float, float, float, float],
    samples: int,
    seed: int,
    force_download: bool,
) -> dict:
    sources = tuple(dict.fromkeys(COLUMNS[name].source for name in columns))
    source_rules = {
        source: any(COLUMNS[name].positive for name in columns if COLUMNS[name].source == source)
        for source in sources
    }

    outputs = open_output_arrays(directory, columns, samples)
    rng = np.random.default_rng(seed)
    written = 0
    depth_counts: dict[str, int] = {}

    try:
        with make_client() as session:
            for depth_index, depth in enumerate(depths):
                remaining = samples - written
                if remaining == 0:
                    break

                depths_left = len(depths) - depth_index
                target = math.ceil(remaining / depths_left)
                paths = layer_paths(cache_dir, sources, depth, bounds)

                for source, path in paths.items():
                    download_coverage(
                        session,
                        source,
                        depth,
                        bounds,
                        path,
                        force=force_download,
                    )

                shape = validate_grid(paths)
                mask = valid_mask(paths, source_rules)
                selected = select_indices(mask, target, rng)

                if selected.size == 0:
                    print(f'{depth}: no common valid pixels, skipping')
                    depth_counts[depth] = 0
                    continue

                written = fill_slice(
                    outputs,
                    columns,
                    paths,
                    selected,
                    written,
                )
                depth_counts[depth] = int(selected.size)
                print(
                    f'{depth}: selected {selected.size:,} / '
                    f'{mask.size:,} pixels from {shape[1]}x{shape[0]} grid',
                )

        if written != samples:
            msg = (
                f'Only {written:,} common valid samples were available, '
                f'but {samples:,} were requested. Increase --bounds, add depths, '
                'or reduce --samples.'
            )
            raise SystemExit(msg)

        for output in outputs.values():
            output.flush()
    finally:
        outputs.clear()

    return {
        'format_version': 1,
        'purpose': 'ptfkit performance benchmarks',
        'source': {
            'dataset': 'SoilGrids',
            'service': 'WCS 2.0.1',
            'endpoint': WCS_URL,
            'prediction': 'mean',
        },
        'sampling': {
            'samples': samples,
            'seed': seed,
            'depths': list(depths),
            'samples_per_depth': depth_counts,
            'bounds_epsg_152160': list(bounds),
        },
        'storage': {
            'array_format': 'NPY 1.0',
            'dtype': '<f8',
            'shape': [samples],
            'order': 'C',
        },
        'columns': {
            name: {
                'file': f'{name}.npy',
                'unit': COLUMNS[name].unit,
                'soilgrids_property': COLUMNS[name].source,
                'scale_from_soilgrids_integer': COLUMNS[name].scale,
                'description': COLUMNS[name].description,
            }
            for name in columns
        },
    }


def write_manifest(directory: Path, manifest: dict) -> None:
    with directory.joinpath('manifest.json').open('w', encoding='utf-8') as file:
        json.dump(manifest, file, indent=2)


def add_deterministic_file(
    archive: tarfile.TarFile,
    path: Path,
    arcname: str,
) -> None:
    stat = path.stat()
    info = tarfile.TarInfo(arcname)
    info.size = stat.st_size
    info.mode = 0o644
    info.mtime = 0
    info.uid = 0
    info.gid = 0
    info.uname = ''
    info.gname = ''

    with path.open('rb') as file:
        archive.addfile(info, file)


def compress_dataset(
    directory: Path,
    output: Path,
    *,
    level: int,
) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    partial = output.with_suffix(output.suffix + '.part')
    partial.unlink(missing_ok=True)

    print(f'Compressing {output}')
    with tarfile.open(partial, mode='w:zst', level=level) as archive:  # ty: ignore[invalid-argument-type]
        for path in sorted(directory.iterdir(), key=lambda item: item.name):
            if path.is_file():
                add_deterministic_file(archive, path, path.name)

    partial.replace(output)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open('rb') as file:
        while chunk := file.read(8 * 1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def format_bytes(size: int) -> str:
    value = float(size)
    for unit in ('B', 'KiB', 'MiB', 'GiB', 'TiB'):
        if value < 1024.0 or unit == 'TiB':  # noqa: PLR2004
            return f'{value:.1f} {unit}'
        value /= 1024.0
    raise AssertionError


def main() -> None:
    args = parse_args()

    output = args.output.resolve()
    cache_dir = args.cache_dir.resolve()
    columns = tuple(dict.fromkeys(args.columns))
    depths = tuple(dict.fromkeys(args.depths))
    bounds = tuple(args.bounds)

    xmin, ymin, xmax, ymax = bounds
    if xmin >= xmax or ymin >= ymax:
        msg = 'bounds must satisfy XMIN < XMAX and YMIN < YMAX'
        raise SystemExit(msg)

    with tempfile.TemporaryDirectory(prefix='ptfkit-soilgrids-') as temporary:
        dataset_dir = Path(temporary) / 'soilgrids'
        dataset_dir.mkdir()

        manifest = prepare_arrays(
            directory=dataset_dir,
            cache_dir=cache_dir,
            columns=columns,
            depths=depths,
            bounds=bounds,
            samples=args.samples,
            seed=args.seed,
            force_download=args.force_download,
        )
        write_manifest(dataset_dir, manifest)
        compress_dataset(dataset_dir, output, level=args.zstd_level)

    print(f'Wrote {output}')
    print(f'Size: {format_bytes(output.stat().st_size)}')
    print(f'SHA-256: {sha256(output)}')


if __name__ == '__main__':
    main()
