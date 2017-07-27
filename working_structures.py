from configman import (
    configuration,
    Namespace,
    RequiredConfig,
    class_converter,
)


class URLStatsCounter(RequiredConfig):
    def __init__(self, config):
        self.config = config
        self.count = 0

    def increment_count(self, amount=1):
        self.count += amount

    def subsume(self, other_URLStatsCounter):
        self.count += other_URLStatsCounter.count

class URLStatsCounterWithProbability(URLStatsCounter):
    def __init__(self, config):
        super(URLStatsCounterWithProbability, self).__init__(config)
        self.p = 0;
        self.o = 0;

    def subsume(self, other_URLStatsCounter):
        super(URLStatsCounterWithProbability, self).subsume(other_URLStatsCounter)
        self.p = other_URLStatsCounter.p  # TODO: not correct action
        self.o = other_URLStatsCounter.o  # TODO: not correct action


class URLs(RequiredConfig):
    required_config = Namespace()
    required_config.add_option(
        name="url_stats_class",
        default="URLStats",
        from_string_converter=class_converter,
        description="dependency injection of a class to represent statistics for URLs"
    )

    def __init__(self, config):
        self.config = config
        self.urls = {}



class QueryURLDatabase(RequiredConfig):
    required_config = Namespace()
    required_config.add_option(
        name="url_class",
        default="URLs",
        from_string_converter=class_converter,
        description="dependency injection of a class to represent URLs"
    )
    def __init__(self, config):
        self.config = config
        self.queriesAndUrls = {}


    def __iter__(self):

