import taichi as ti
from tolvera import Tolvera


@ti.data_oriented
class Attract:
    """
    Move all active particles toward the center of mass.
    """

    def __init__(self, tolvera: Tolvera, **kwargs):
        self.tv = tolvera
        self.kwargs = kwargs
        self.tv.s.com_s = {
            "state": {"com": (ti.math.vec2, None, None)},
            "shape": self.tv.sn,
            "randomise": False,
        }

        self.tv.s.attract_s = {
            "state": {"com": (ti.f32, -1.0, 1.0)},
            "shape": (self.tv.sn, self.tv.sn),
            "randomise": True,
        }
        pass

    @ti.kernel
    def step(self, particles: ti.template(), weight: ti.f32):
        n = particles.shape[0]
        n_per_species = n // self.tv.sn
        specie_list = []

        # Compute Center of Mass for each species
        for i in range(n):
            if particles[i].active == 1:
                self.tv.s.com_s[particles[i].species].com += particles[i].pos

        for specie in range(self.tv.sn):
            self.tv.s.com_s[specie].com /= n_per_species

        for i in range(n):
            com = self.tv.s.com_s[particles[i].species].com
            if particles[i].active == 1:
                direction = (com - particles[i].pos).normalized()
                particles[i].vel += direction * weight * particles[i].speed
                particles[i].pos += particles[i].vel

                interaction_force = ti.Vector([0.0, 0.0])
                for s in range(self.tv.sn):
                    if s != particles[i].species:  # Other species influence
                        com_other = self.tv.s.com_s[s].com
                        attraction_factor = self.tv.s.attract_s[
                            particles[i].species, s
                        ].com
                        interaction_force += (
                            attraction_factor * (com_other - particles[i].pos)
                        ).normalized()

                interaction_force *= 0.5
                particles[i].vel += (
                    (direction + interaction_force).normalized()
                    * weight
                    * particles[i].speed
                )
                particles[i].pos += particles[i].vel

        # Reset Center  of Mass
        for s in range(self.tv.sn):
            self.tv.s.com_s[s].com = ti.Vector([0.0, 0.0])

    def __call__(self, px, weight: ti.f32 = 1.0):
        self.step(self.tv.p.field, px, weight)
