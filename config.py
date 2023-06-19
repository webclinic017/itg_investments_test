from dataclasses import dataclass
from environs import Env


@dataclass
class BinanceConfig:
    api_key: str
    api_secret: str
    api_testnet: str
    api_testnet_secret: str


@dataclass
class Config:
    binance_api: BinanceConfig


def load_config(path: str = None):
    env = Env()
    env.read_env(path)

    return Config(
        binance_api=BinanceConfig(
            api_key=env.str('api_key'),
            api_secret=env.str('api_secret'),
            api_testnet=env.str('api_testnet'),
            api_testnet_secret=env.str('api_testnet_secret')
        ),
    )
