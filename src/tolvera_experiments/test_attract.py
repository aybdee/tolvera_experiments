import taichi as ti
from tolvera import Tolvera, run

from tolvera_experiments.attract import Attract


def main(**kwargs):
    tv = Tolvera(**kwargs)
    attraction = Attract(tv)

    @tv.render
    def _():
        tv.px.diffuse(0.99)
        tv.px.particles(tv.p, tv.s.species)
        attraction()
        return tv.px


if __name__ == "__main__":
    run(main)
