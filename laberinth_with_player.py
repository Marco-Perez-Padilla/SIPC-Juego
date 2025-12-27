import sys
import pygame
import pymunk
import pymunk.pygame_util


WALL_COLOR = (200, 50, 50, 255)         # rojo
INNER_WALL_COLOR = (50, 50, 200, 255)   # azul
OBSTACLE_COLOR = (0, 150, 0, 255)       # verde
DOOR_COLOR = (50, 50, 200, 255)         # azul
PLAYER_COLOR = (0, 0, 0, 255)           # negro


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


def add_obstacle_ball(space, pos, radius=18, mass=8, friction=1.2):
    body = pymunk.Body()
    body.position = pos

    shape = pymunk.Circle(body, radius)
    shape.mass = mass
    shape.friction = friction
    shape.elasticity = 0.0
    shape.color = OBSTACLE_COLOR

    space.add(body, shape)
    return shape


def add_door(
    space,
    p1, p2,
    thickness=5,
    mass=5,
    friction=1.0,
    max_angle_degrees=70,
    spring_stiffness=60000,
    spring_damping=2000,
    color=DOOR_COLOR
):
    hinge_body = pymunk.Body(body_type=pymunk.Body.STATIC)
    hinge_body.position = p1

    mid = ((p1[0] + p2[0]) / 2.0, (p1[1] + p2[1]) / 2.0)

    a_local = (p1[0] - mid[0], p1[1] - mid[1])
    b_local = (p2[0] - mid[0], p2[1] - mid[1])

    moment = pymunk.moment_for_segment(mass, a_local, b_local, thickness)

    door_body = pymunk.Body(mass, moment)
    door_body.position = mid

    door_shape = pymunk.Segment(door_body, a_local, b_local, thickness)
    door_shape.friction = friction
    door_shape.elasticity = 0.0
    door_shape.color = color

    hinge_joint = pymunk.PinJoint(door_body, hinge_body, a_local, (0, 0))

    spring = pymunk.DampedRotarySpring(
        door_body, hinge_body,
        rest_angle=0.0,
        stiffness=spring_stiffness,
        damping=spring_damping
    )

    max_angle = max_angle_degrees * (3.141592653589793 / 180.0)
    limit = pymunk.RotaryLimitJoint(door_body, hinge_body, -max_angle, max_angle)

    space.add(hinge_body, door_body, door_shape, hinge_joint, spring, limit)
    return door_shape


def add_player(space, pos, radius=14, mass=3, friction=1):
    """
    Esfera negra controlable. Por ahora es física normal (dinámica),
    así colisiona y puede empujar obstáculos/puertas.
    """
    body = pymunk.Body()
    body.position = pos

    shape = pymunk.Circle(body, radius)
    shape.mass = mass
    shape.friction = friction
    shape.elasticity = 0.0
    shape.color = PLAYER_COLOR

    space.add(body, shape)
    return shape


def main():
    pygame.init()
    W, H = 750, 750
    screen = pygame.display.set_mode((W, H))
    pygame.display.set_caption("Laberinto - jugador WASD + puertas + obstáculo")
    clock = pygame.time.Clock()

    space = pymunk.Space()
    space.gravity = (0.0, 0.0)
    space.damping = 0.8  # rozamiento del "suelo"

    add_outer_walls(space, W, H, thickness=5, margin=0)

    inner_segments = [
        ((0, 650), (250, 650)),
        ((350, 550), (350, 750)),
        ((450, 650), (650, 650)),
        ((650, 450), (650, 650)),
        ((100, 350), (100, 550)),
        ((100, 550), (250, 550)),
        ((250, 550), (250, 350)),
        ((250, 450), (450, 450)),
        ((450, 450), (450, 550)),
        ((450, 550), (550, 550)),
        ((450, 250), (550, 250)),
        ((0, 250), (350, 250)),
        ((250, 350), (350, 350)),
        ((175, 100), (175, 450)),
        ((100, 0), (100, 175)),
        ((250, 0), (250, 175)),
        ((350, 0), (350, 175)),
        ((450, 60), (450, 175)),
        ((350, 150), (450, 150)),
        ((650, 60), (650, 150)),
        ((550, 150), (650, 150)),
        ((550, 150), (550, 450)),
        ((450, 350), (650, 350)),
        ((650, 250), (750, 250)),
        ((650, 450), (750, 450)),
        ((550, 0), (550, 150)),
    ]
    add_wall_segments(space, inner_segments, thickness=5)

    # Puertas (p1 es la bisagra)
    door_segments = [
        ((550, 740), (550, 660)),
        ((740, 150), (660, 150)),
        ((100, 240), (100, 185)),
        ((100, 740), (100, 660)),
    ]
    for p1, p2 in door_segments:
        add_door(space, p1, p2, thickness=5, mass=5, max_angle_degrees=90)

    # Obstáculo empujable
    add_obstacle_ball(space, pos=(400, 300), radius=43, mass=10)

    # Jugador (elige el punto exacto de spawn)
    player = add_player(space, pos=(50, 700), radius=20, mass=3)

    draw_options = pymunk.pygame_util.DrawOptions(screen)

    # --- Control WASD ---
    SPEED = 150  # píxeles/seg aprox (ajusta a gusto)

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sys.exit(0)
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                sys.exit(0)

        # Leer teclas mantenidas
        keys = pygame.key.get_pressed()
        vx = 0
        vy = 0
        if keys[pygame.K_a]:
            vx -= SPEED
        if keys[pygame.K_d]:
            vx += SPEED
        if keys[pygame.K_w]:
            vy -= SPEED
        if keys[pygame.K_s]:
            vy += SPEED

        # Control simple: fijamos velocidad (fácil y estable para top-down)
        player.body.velocity = (vx, vy)

        screen.fill((255, 255, 255))
        space.debug_draw(draw_options)

        DT = 1/50.0
        SUBSTEPS = 5
        for _ in range(SUBSTEPS):
          space.step(DT / SUBSTEPS)
        pygame.display.flip()
        clock.tick(50)


if __name__ == "__main__":
    main()
