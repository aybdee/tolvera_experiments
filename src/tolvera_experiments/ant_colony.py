import taichi as ti
import taichi.math as tm
import random
from typing import Literal
from tolvera.pixels import Pixels


@ti.data_oriented
class AntColony:
    def __init__(self, tolvera, **kwargs):
        self.tv = tolvera
        self.tv.s.food_pheromone_w = {
            "state": {
                "direction": (ti.math.vec2, -1.0, 1.0),  # Direction of pheromone
                "intensity": (ti.f32, 0.0, 1.0),  # Strength of pheromone
            },
            "shape": (self.tv.x, self.tv.y),
            "randomise": False,
        }

        self.tv.s.nest_pheromone_w = {
            "state": {
                "direction": (ti.math.vec2, -1.0, 1.0),  # Direction of pheromone
                "intensity": (ti.f32, 0.0, 1.0),  # Strength of pheromone
            },
            "shape": (self.tv.x, self.tv.y),
            "randomise": False,
        }

        self.tv.s.food_w = {
            "state": {"has_food": (ti.i32, 0, 1)},
            "shape": (self.tv.x, self.tv.y),
            "randomise": False,
        }

        self.tv.s.ant_p = {
            "state": {
                "direction": (ti.math.vec2, -1.0, 1.0),
                "has_food": (ti.i32, 0, 1),
            },
            "shape": self.tv.pn,
            "randomise": False,
        }

        self.tv.s.ant_p.randomise_attr("direction")
        self.nest_pos = ti.Vector(
            [random.uniform(0, self.tv.x), random.uniform(0, self.tv.y)]
        )
        self.nest_size = 200
        self.n_food = 10
        self.food_sources = ti.Struct.field(
            {"pos": ti.math.vec2, "size": ti.f32}, shape=self.n_food
        )
        self.initialize_food()
        self.initialize_ants(self.tv.p.field)

        self.nest_view = Pixels(tolvera, **kwargs)

    @ti.kernel
    def initialize_food(self):
        for i in range(self.n_food):
            self.food_sources[i].pos = ti.Vector(
                [ti.random() * self.tv.x, ti.random() * self.tv.y]
            )
            self.food_sources[i].size = (
                ti.random() * 150 + 100
            )  # random size between 100 and 250

    @ti.func
    def is_on_food(self, pos) -> ti.i32:
        # Check if the position overlaps with any food source
        found_food = 0
        for i in ti.static(range(self.n_food)):
            if (pos - self.food_sources[i].pos).norm() <= self.food_sources[i].size:
                found_food = 1
        return found_food

    @ti.func
    def is_on_nest(self, pos) -> ti.i32:
        # Check if the position overlaps with any food source
        at_nest = 0
        for _ in ti.static(range(self.n_food)):
            if (pos - self.nest_pos).norm() <= self.nest_size:
                at_nest = 1
        return at_nest

    @ti.func
    def deposit_pheromone(self, pos, direction, has_food):
        grid_position = self.position_to_grid(pos)

        # The pheromone direction should point **backward** toward the source
        pheromone_direction = -direction  # Invert direction to point back to source
        current_intensity = 0.0
        new_direction = ti.Vector([0.0, 0.0])
        current_direction = ti.Vector([0.0, 0.0])

        if has_food:
            # Reference the correct pheromone grid
            current_intensity = self.tv.s.food_pheromone_w[
                grid_position.x, grid_position.y
            ].intensity
            current_direction = self.tv.s.food_pheromone_w[
                grid_position.x, grid_position.y
            ].direction
        else:
            current_intensity = self.tv.s.nest_pheromone_w[
                grid_position.x, grid_position.y
            ].intensity
            current_direction = self.tv.s.nest_pheromone_w[
                grid_position.x, grid_position.y
            ].direction

        # Deposit a small amount of pheromone
        deposit_amount = 0.1
        new_intensity = min(current_intensity + deposit_amount, 1.0)  # Clamp to max 1.0

        # Compute weights for blending based on intensity
        total_intensity = current_intensity + deposit_amount
        if total_intensity > 0:
            weight_current = current_intensity / total_intensity
            weight_new = deposit_amount / total_intensity
            new_direction = (
                weight_current * current_direction + weight_new * pheromone_direction
            ).normalized()
        else:
            new_direction = (
                pheromone_direction  # If no existing pheromone, set directly
            )

        # Update the correct pheromone grid
        if has_food:
            self.tv.s.food_pheromone_w[grid_position.x, grid_position.y].intensity = (
                new_intensity
            )
            self.tv.s.food_pheromone_w[grid_position.x, grid_position.y].direction = (
                new_direction
            )
        else:
            self.tv.s.nest_pheromone_w[grid_position.x, grid_position.y].intensity = (
                new_intensity
            )
            self.tv.s.nest_pheromone_w[grid_position.x, grid_position.y].direction = (
                new_direction
            )

    @ti.func
    def position_to_grid(self, pos):
        x = ti.round(pos[0]) % self.tv.x
        y = ti.round(pos[1]) % self.tv.y
        return ti.Vector([x, y])

    @ti.kernel
    def move_ants(self, particles: ti.template()):
        for i in range(self.tv.pn):
            pos = particles[i].pos
            direction = self.tv.s.ant_p[i].direction
            new_direction = direction

            # Check if there is food at the current position
            if self.is_on_food(pos) and self.tv.s.ant_p[i].has_food == 0:
                self.tv.s.ant_p[i].has_food = 1
                # When finding food, reverse direction to head back to nest
                new_direction = self.nest_pos - pos

            if self.is_on_nest(pos) and self.tv.s.ant_p[i].has_food == 1:
                self.tv.s.ant_p[i].has_food = 0
                # When dropping food at nest, add some randomness to find food again
                new_direction = ti.Vector(
                    [ti.random() * 2 - 1, ti.random() * 2 - 1]
                ).normalized()

            # Choose direction based on pheromones and current state
            chosen_direction = self.choose_direction(
                pos, new_direction, self.tv.s.ant_p[i].has_food
            )

            # Apply the chosen direction
            new_pos = pos + chosen_direction * 3.0

            # Deposit pheromone at the new position
            self.deposit_pheromone(
                new_pos, chosen_direction, self.tv.s.ant_p[i].has_food
            )

            # update particle
            self.tv.s.ant_p[i].direction = chosen_direction
            particles[i].vel = chosen_direction * 3.0
            particles[i].pos += particles[i].vel

    @ti.kernel
    def draw_pheromone(self):
        for i, j in self.tv.s.food_pheromone_w.field:
            # Get intensities
            food_intensity = self.tv.s.food_pheromone_w.field[i, j].intensity
            nest_intensity = self.tv.s.nest_pheromone_w.field[i, j].intensity

            # Default to black (no pheromone)
            color = ti.Vector([0.0, 0.0, 0.0, 1.0])

            # Draw the stronger pheromone
            if food_intensity > nest_intensity:
                # Red for food pheromone
                color = ti.Vector([1.0, 0.0, 0.0, food_intensity * 0.5])
            elif nest_intensity > 0:
                # Blue for nest pheromone
                color = ti.Vector([0.0, 0.0, 1.0, nest_intensity * 0.5])
            if food_intensity > 0 or nest_intensity > 0:
                self.tv.px.px.rgba[i, j] = color

    @ti.kernel
    def decay_pheromones(self, decay_rate: ti.f32):
        for i, j in self.tv.s.food_pheromone_w.field:
            # Decay food pheromone
            self.tv.s.food_pheromone_w.field[i, j].intensity *= decay_rate

            # Decay nest pheromone
            self.tv.s.nest_pheromone_w.field[i, j].intensity *= decay_rate

    @ti.kernel
    def draw_nest(self):
        # Draw food sources as red circles
        for i in range(self.n_food):  # Loop through all food sources
            food_pos = self.food_sources[i].pos
            food_size = self.food_sources[i].size
            self.nest_view.rect(
                food_pos[0] - food_size / 2,
                food_pos[1] - food_size / 2,
                food_size,
                food_size,
                ti.Vector([1.0, 0.0, 0.0, 1.0]),  # Red color
            )

        # Draw nest as a blue square
        self.nest_view.rect(
            self.nest_pos[0] - self.nest_size / 2,  # Centering the nest
            self.nest_pos[1] - self.nest_size / 2,
            self.nest_size,
            self.nest_size,
            ti.Vector([0.0, 0.0, 1.0, 1.0]),  # Blue color
        )

    def show_nest(self):
        self.draw_nest()
        return self.nest_view

    @ti.func
    def choose_direction(self, pos, current_direction, has_food):
        intensities, directions = self.get_pheromones(pos, has_food)

        total_intensity = 0.0
        for i in ti.static(range(8)):  # Unroll loop for better performance
            total_intensity += intensities[i]

        chosen_direction = current_direction  # Default: keep moving forward

        # Always add some randomness/exploration whether following pheromones or not
        explore_prob = 0.3
        explore_rate = 0.2

        if total_intensity > 0.01:  # Only follow pheromones if significant intensity
            print("following pheronomes")
            # Compute probabilities
            probabilities = ti.Vector.zero(float, 8)
            for i in ti.static(range(8)):
                probabilities[i] = intensities[i] / total_intensity

            rand_val = ti.random()
            cumulative = 0.0
            selected_index = 0

            for i in ti.static(range(8)):
                cumulative += probabilities[i]
                selected_index = ti.select(rand_val < cumulative, i, selected_index)

            selected_index = ti.cast(selected_index, ti.i32)
            chosen_direction = ti.Vector(
                [directions[selected_index, 0], directions[selected_index, 1]]
            )

            # Add some random perturbation to avoid freezing
            if ti.random() < explore_prob:
                rand_angle = (ti.random() - 0.5) * ti.math.pi * explore_rate
                c, s = tm.cos(rand_angle), tm.sin(rand_angle)
                chosen_direction = ti.Vector(
                    [
                        chosen_direction[0] * c - chosen_direction[1] * s,
                        chosen_direction[0] * s + chosen_direction[1] * c,
                    ]
                )
        else:
            # No significant pheromones, continue with current direction plus some randomness
            if ti.random() < 0.8:  # Higher chance of exploring when no pheromones
                rand_angle = (ti.random() - 0.5) * ti.math.pi * 0.7
                c, s = tm.cos(rand_angle), tm.sin(rand_angle)
                chosen_direction = ti.Vector(
                    [
                        current_direction[0] * c - current_direction[1] * s,
                        current_direction[0] * s + current_direction[1] * c,
                    ]
                )

        return chosen_direction.normalized()

    @ti.func
    def get_pheromones(self, pos, has_food):
        """Sample pheromone intensities in 8 directions using nearest-neighbor lookup"""
        directions = (
            ti.Vector([-1, -1]),
            ti.Vector([0, -1]),
            ti.Vector([1, -1]),
            ti.Vector([-1, 0]),
            ti.Vector([1, 0]),
            ti.Vector([-1, 1]),
            ti.Vector([0, 1]),
            ti.Vector([1, 1]),
        )
        intensities = ti.Vector.zero(float, 8)  # Store pheromone intensities
        directions_out = ti.Matrix.zero(float, 8, 2)  # Store 8 direction vectors

        for i in ti.static(range(8)):
            sample_dir = directions[i]
            new_pos = pos + sample_dir
            x = tm.mod(ti.cast(ti.floor(new_pos.x), ti.i32), self.tv.x)
            y = tm.mod(ti.cast(ti.floor(new_pos.y), ti.i32), self.tv.y)

            if has_food:
                intensities[i] = self.tv.s.nest_pheromone_w[x, y].intensity
                pheromone_dir = self.tv.s.nest_pheromone_w[x, y].direction
                directions_out[i, 0] = pheromone_dir[0]
                directions_out[i, 1] = pheromone_dir[1]
            else:
                intensities[i] = self.tv.s.food_pheromone_w[x, y].intensity
                pheromone_dir = self.tv.s.food_pheromone_w[x, y].direction
                directions_out[i, 0] = pheromone_dir[0]
                directions_out[i, 1] = pheromone_dir[1]

        return intensities, directions_out

    @ti.kernel
    def initialize_ants(self, particles: ti.template()):
        for i in range(self.tv.pn):
            particles[i].pos = self.nest_pos
            # Initialize with random directions away from nest
            angle = ti.random() * 2 * ti.math.pi
            self.tv.s.ant_p[i].direction = ti.Vector([tm.cos(angle), tm.sin(angle)])

    def step(self):
        self.draw_pheromone()
        self.decay_pheromones(0.99)
        self.move_ants(self.tv.p.field)
        pass

    def __call__(self, view: Literal["ANTS"] | Literal["NEST"]):
        if view == "ANTS":
            self.step()
            return self.tv.px
        else:
            return self.show_nest()
