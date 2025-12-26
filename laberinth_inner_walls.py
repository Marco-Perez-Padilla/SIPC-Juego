import sys
import pygame
import pymunk
import pymunk.pygame_util


WALL_COLOR = (200, 50, 50, 255)      # rojo
INNER_WALL_COLOR = (50, 50, 200, 255) # azul


def add_outer_walls(space, width, height, thickness=5, margin=10):
    body = space.static_body
    left, right = margin, width - margin
    top, bottom = margin, height - margin

    walls = [
        pymunk.Segment(body, (left, top), (right, top), thickness),
        pymunk.Segment(body, (left, bottom), (right, bottom), thickness),
        pymunk.Segment(body, (left, top), (left, bottom), thickness),
        pymunk.Segment(body, (right, top), (right, bottom), thickness),
    ]
    for w in walls:
        w.friction = 1.0
        w.elasticity = 0.0
        w.color = WALL_COLOR

    space.add(*walls)
    return walls


def add_wall_segments(space, segments, thickness=8, color=INNER_WALL_COLOR):
    """
    segments: lista de tuplas ((x1,y1), (x2,y2)) para cada pared
    """
    body = space.static_body
    walls = []
    for (p1, p2) in segments:
        s = pymunk.Segment(body, p1, p2, thickness)
        s.friction = 1.0
        s.elasticity = 0.0
        s.color = color
        walls.append(s)

    space.add(*walls)
    return walls


def main():
    pygame.init()
    W, H = 750, 750
    screen = pygame.display.set_mode((W, H))
    pygame.display.set_caption("Laberinto - paredes exteriores + interiores")
    clock = pygame.time.Clock()

    space = pymunk.Space()
    space.gravity = (0.0, 0.0)

    add_outer_walls(space, W, H, thickness=5, margin=0)

    # ✅ Paredes internas (ejemplo básico de pasillos)
    inner_segments = [
        ((0, 650), (250, 650)),
        ((350, 550), (350, 750)),
        ((550, 650), (550, 750)),
        ((450, 650), (650, 650)),
        ((650, 550), (650, 650)),
        ((100, 350), (100, 550)),
        ((100, 350), (100, 550)),
        ((100, 550), (250, 550)),
        ((250, 550), (250, 350)),
        ((250, 450), (450, 450)),
        ((450, 450), (450, 550)),
        ((450, 550), (550, 550)),
        ((0, 250), (450, 250)),
        ((175, 100), (175, 450)),
        ((100, 0), (100, 150)),
        ((250, 0), (250, 150)),
        ((350, 0), (350, 200)),
        ((350, 100), (450, 100)),
        ((650, 0), (650, 150)),
        ((550, 150), (650, 150)),
        ((550, 150), (550, 450)),
        ((350, 350), (650, 350)),
        ((650, 250), (750, 250)),
        ((650, 450), (750, 450)),
        ((525, 0), (525, 100)),
    ]
    add_wall_segments(space, inner_segments, thickness=5)

    draw_options = pymunk.pygame_util.DrawOptions(screen)

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sys.exit(0)
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                sys.exit(0)

        screen.fill((255, 255, 255))
        space.debug_draw(draw_options)

        space.step(1 / 50.0)
        pygame.display.flip()
        clock.tick(50)


if __name__ == "__main__":
    main()
