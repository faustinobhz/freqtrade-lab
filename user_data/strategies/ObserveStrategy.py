"""Valida dados, inicialização e interface. Não gera ordens de entrada."""
from pandas import DataFrame
from freqtrade.strategy import IStrategy


class ObserveStrategy(IStrategy):
    INTERFACE_VERSION = 3
    timeframe = "5m"
    can_short = False
    startup_candle_count = 20
    minimal_roi = {"0": 0.02}
    stoploss = -0.02
    process_only_new_candles = True

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["sma20"] = dataframe["close"].rolling(20).mean()
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["enter_long"] = 0
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["exit_long"] = 0
        return dataframe

