import json

from augur.__version__ import __version__
from augur.__version__ import is_augur_version_compatible
from augur.validate import validate_json, ValidateError, load_json_schema


FILTERED_ATTRS = ["generated_by"]


class NodeDataFile:
    def __init__(self, fname):
        self.fname = fname

        with open(fname, encoding="utf-8") as jfile:
            self.attrs = json.load(jfile)

        self.validate()

    @property
    def annotations(self):
        return self.attrs.get("annotations")

    @property
    def nodes(self):
        return self.attrs.get("nodes")

    @property
    def generated_by(self):
        return self.attrs.get("generated_by")

    @property
    def is_generated_by_incompatible_augur(self):
        if not isinstance(self.generated_by, dict):
            # If it's not a dict created by augur, we can't reliably classify it as incompatible
            return False

        generated_by_augur = self.generated_by.get("program") == "augur"
        compatible_version = is_augur_version_compatible(
            self.generated_by.get("version")
        )

        return generated_by_augur and not compatible_version

    def items(self):
        filtered_attrs = {
            key: value for key, value in self.attrs.items() if key not in FILTERED_ATTRS
        }

        return filtered_attrs.items()

    def validate(self):
        if self.annotations:
            try:
                validate_json(
                    self.annotations,
                    load_json_schema("schema-annotations.json"),
                    self.fname,
                )
            except ValidateError as err:
                raise RuntimeError(
                    f"{self.fname} contains an `annotations` attribute of an invalid JSON format. Was it "
                    "produced by different version of augur the one you are currently using "
                    f" ({__version__})? Please check the program that produced that JSON file."
                ) from err

        if not isinstance(self.nodes, dict):
            raise RuntimeError(
                f"`nodes` value in {self.fname} is not a dictionary. Please check the formatting of this JSON!"
            )

        if self.is_generated_by_incompatible_augur:
            raise RuntimeError(
                f"Augur version incompatibility detected: the JSON {self.fname} was generated by "
                f"{self.generated_by}, which is incompatible with the current augur version "
                f"({__version__}). We suggest you rerun the pipeline using the current version of "
                "augur."
            )