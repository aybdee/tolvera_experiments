import taichi as ti
from taichi.ui import PRESS
from tolvera import Tolvera, run
from tolvera_experiments import ant_colony
from tolvera_experiments.ant_colony import AntColony

ti.init(debug=True)


def main(**kwargs):
    tv = Tolvera(**kwargs)
    ant_colony = AntColony(tv, **kwargs)

    # Initialize view state
    view_state = {"current": "ANTS", "press": 0}

    @tv.render
    def _():
        # Process events from tv.window
        for e in tv.ti.window.get_events():
            if view_state["press"] == 0:
                if e.key == ti.GUI.SPACE:
                    view_state["current"] = (
                        "NEST" if view_state["current"] == "ANTS" else "ANTS"
                    )
                    print(f"Switched to {view_state['current']} view")
                view_state["press"] = 1
            else:
                view_state["press"] = 0

        tv.px.particles(tv.p, tv.s.species)
        tv.px.diffuse(0.99)

        return ant_colony(view_state["current"])


if __name__ == "__main__":
    run(main)
