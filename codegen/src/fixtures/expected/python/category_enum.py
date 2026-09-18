


class TestCategory(Enum):
    """Test category type.

    Attributes:
        FIRST: First test category.

    """

    FIRST = "first"

    @classmethod
    def array(cls, values: Iterable[TestCategory]) -> EnumArray[TestCategory]:
        """Encode members once as a reusable typed enum array."""
        return EnumArray._from_members(cls, values)  # noqa: SLF001
