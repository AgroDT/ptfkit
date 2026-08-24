//! Target-specific text parsing for generated categorical adapters.

use std::{fmt, str::FromStr};

pub use crate::adapters_generated::{UsdaTexture, UsdaTextureFractions};

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct ParseUsdaTextureError;

impl fmt::Display for ParseUsdaTextureError {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter.write_str("invalid exact USDA texture class")
    }
}

impl std::error::Error for ParseUsdaTextureError {}

impl FromStr for UsdaTexture {
    type Err = ParseUsdaTextureError;

    fn from_str(value: &str) -> Result<Self, Self::Err> {
        match value {
            "sand" => Ok(Self::Sand),
            "loamy sand" => Ok(Self::LoamySand),
            "sandy loam" => Ok(Self::SandyLoam),
            "loam" => Ok(Self::Loam),
            "silt loam" => Ok(Self::SiltLoam),
            "silt" => Ok(Self::Silt),
            "sandy clay loam" => Ok(Self::SandyClayLoam),
            "clay loam" => Ok(Self::ClayLoam),
            "silty clay loam" => Ok(Self::SiltyClayLoam),
            "sandy clay" => Ok(Self::SandyClay),
            "silty clay" => Ok(Self::SiltyClay),
            "clay" => Ok(Self::Clay),
            _ => Err(ParseUsdaTextureError),
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn parsing_is_exact() {
        assert_eq!("loam".parse(), Ok(UsdaTexture::Loam));
        for invalid in ["Loam", " loam", "loam ", "sandy-loam", "sandy_loam", "L"] {
            assert!(invalid.parse::<UsdaTexture>().is_err());
        }
    }
}
