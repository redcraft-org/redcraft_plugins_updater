import unittest

from utils.file_filters import compile_file_filter


class FileFiltersTests(unittest.TestCase):
    def test_glob_filters_match_real_file_names(self):
        # Real filters from redcraft_plugins.json against real artifact names
        matches = [
            ("waterfall-1.20-*.jar", "waterfall-1.20-508.jar"),
            ("LuckPerms-Bukkit-*.jar", "LuckPerms-Bukkit-5.4.119.jar"),
            ("spark-*-bukkit.jar", "spark-1.10.53-bukkit.jar"),
            ("BlueMap-*-cli.jar", "BlueMap-5.3-cli.jar"),
            (
                "carpet-tis-addition-mc1.20.4-*.jar",
                "carpet-tis-addition-mc1.20.4-v1.62.0.jar",
            ),
            ("target/Citizens-*.jar", "target/Citizens-2.0.33-b3419.jar"),
            ("WorldBorder.jar", "WorldBorder.jar"),
        ]

        for file_filter, file_name in matches:
            self.assertIsNotNone(
                compile_file_filter(file_filter).match(file_name),
                "{} should match {}".format(file_filter, file_name),
            )

    def test_glob_filters_treat_dots_as_literals(self):
        filter_regex = compile_file_filter("waterfall-1.20-*.jar")

        self.assertIsNone(filter_regex.match("waterfall-1x20-508.jar"))
        self.assertIsNone(filter_regex.match("waterfall-1.20-508xjar"))

    def test_glob_filters_treat_plus_as_literal(self):
        # The old "*" to ".+" substitution turned this filter into ".++",
        # a possessive quantifier that could never match
        filter_regex = compile_file_filter("fabric-api-*+1.20.4.jar")

        self.assertIsNotNone(filter_regex.match("fabric-api-0.96.11+1.20.4.jar"))
        self.assertIsNone(filter_regex.match("fabric-api-0.96.111.20.4.jar"))

    def test_glob_filters_are_anchored(self):
        self.assertIsNone(
            compile_file_filter("spark-*-bukkit.jar").match(
                "spark-1.10.53-bukkit.jar.sha1"
            )
        )
        self.assertIsNone(
            compile_file_filter("WorldBorder.jar").match("WorldBorder.jar.txt")
        )

    def test_regex_filters_are_preserved(self):
        # Real regex filters from redcraft_plugins.json
        filter_regex = compile_file_filter("lithium-fabric-mc1\\.20\\.4-.+\\d+\\.jar")
        self.assertIsNotNone(filter_regex.match("lithium-fabric-mc1.20.4-0.12.1.jar"))

        filter_regex = compile_file_filter("memoryleakfix-*\\d.jar")
        self.assertIsNotNone(
            filter_regex.match("memoryleakfix-fabric-1.20.4-1.1.5.jar")
        )

        filter_regex = compile_file_filter(
            "sodium-fabric-(?!.*api(-dev)?.jar$).*.(jar)"
        )
        self.assertIsNotNone(filter_regex.match("sodium-fabric-0.5.8+mc1.20.4.jar"))
        self.assertIsNone(filter_regex.match("sodium-fabric-0.5.8+mc1.20.4-api.jar"))
