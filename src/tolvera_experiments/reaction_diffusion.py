import taichi as ti
from tolvera import Tolvera, run

from tolvera_experiments.attract import Attract


def main(**kwargs):
    tv = Tolvera(**kwargs)

    @tv.render
    def _():
        tv.px.diffuse(0.99)
        tv.px.set(tv.v.rd())
        return tv.px


if __name__ == "__main__":
    run(main)
