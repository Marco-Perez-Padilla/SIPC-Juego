import sys
import pygame
import pymunk
import pymunk.pygame_util

# Control por mano 
import mediapipe as mp
import cv2
import numpy as np
import hand_force_application as hand_module


# COLORES (RGBA para debug_draw de pymunk)
WALL_COLOR = (200, 50, 50, 255)         # rojo: paredes exteriores
INNER_WALL_COLOR = (50, 50, 200, 255)   # azul: paredes internas
OBSTACLE_COLOR = (0, 150, 0, 255)       # verde: obstáculo empujable
DOOR_COLOR = (50, 50, 200, 255)         # azul: puertas con bisagra
PLAYER_COLOR = (0, 0, 0, 255)           # negro: jugador

KEY_COLOR = (240, 200, 0, 255)          # amarillo: llaves (sensores)
EXIT_DOOR_COLOR = (255, 140, 0, 255)    # naranja: salida (sensor)


#  TIPOS DE COLISIÓN
# Pymunk permite clasificar shapes por collision_type y crear callbacks por tipo.
COLLTYPE_PLAYER = 1
COLLTYPE_KEY = 2
COLLTYPE_EXIT = 3
COLLTYPE_WALL = 4  # paredes (internas y externas)


def add_outer_walls(space, width, height, thickness=5, margin=10):
    """
    Crea las 4 paredes exteriores como segmentos estáticos.
    - Usamos space.static_body: nunca se mueve.
    - collision_type = COLLTYPE_WALL para detectar "muerte" al tocar.
    """
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
        w.collision_type = COLLTYPE_WALL # tocar pared = game over

    space.add(*walls)
    return walls


def add_wall_segments(space, segments, thickness=8, color=INNER_WALL_COLOR):
    """
    Crea paredes internas del laberinto, cada una como Segment estático.
    segments: lista de tuplas [((x1,y1),(x2,y2)), ...]
    """
    body = space.static_body
    walls = []
    for (p1, p2) in segments:
        s = pymunk.Segment(body, p1, p2, thickness)
        s.friction = 1.0
        s.elasticity = 0.0
        s.color = color
        s.collision_type = COLLTYPE_WALL  # tocar pared = game over
        walls.append(s)

    space.add(*walls)
    return walls


def add_obstacle_ball(space, pos, radius=18, mass=8, friction=1.2):
    """
    Obstáculo empujable: círculo dinámico (Body sin body_type => dinámico).
    """
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
    """
    Puerta con bisagra y retorno:
    - p1 es la bisagra (punto fijo).
    - p2 es el extremo libre (se empuja).
    Implementación:
    1) hinge_body: cuerpo estático en p1 (ancla).
    2) door_body: cuerpo dinámico con un Segment.
    3) PinJoint: bisagra.
    4) DampedRotarySpring: "muelle" para volver al ángulo inicial.
    5) RotaryLimitJoint: limita el giro para que no dé vueltas completas.
    """
    hinge_body = pymunk.Body(body_type=pymunk.Body.STATIC)
    hinge_body.position = p1

    # Centro geométrico: colocamos el cuerpo dinámico ahí
    mid = ((p1[0] + p2[0]) / 2.0, (p1[1] + p2[1]) / 2.0)

    # Segmento definido en coordenadas locales del cuerpo de la puerta
    a_local = (p1[0] - mid[0], p1[1] - mid[1])
    b_local = (p2[0] - mid[0], p2[1] - mid[1])

    # Momento de inercia realista para que rote bien
    moment = pymunk.moment_for_segment(mass, a_local, b_local, thickness)

    door_body = pymunk.Body(mass, moment)
    door_body.position = mid

    door_shape = pymunk.Segment(door_body, a_local, b_local, thickness)
    door_shape.friction = friction
    door_shape.elasticity = 0.0
    door_shape.color = color

    # Bisagra en p1: anclamos el punto a_local al (0,0) del hinge_body (que está en p1)
    hinge_joint = pymunk.PinJoint(door_body, hinge_body, a_local, (0, 0))

    # Muelle rotacional que devuelve a rest_angle=0 (posición “cerrada”)
    spring = pymunk.DampedRotarySpring(
        door_body, hinge_body,
        rest_angle=0.0,
        stiffness=spring_stiffness,
        damping=spring_damping
    )

    # Límite de rotación (en radianes)
    max_angle = max_angle_degrees * (3.141592653589793 / 180.0)
    limit = pymunk.RotaryLimitJoint(door_body, hinge_body, -max_angle, max_angle)

    space.add(hinge_body, door_body, door_shape, hinge_joint, spring, limit)
    return door_shape


def add_player(space, pos, radius=14, mass=3, friction=1):
    """
    Jugador: esfera dinámica que colisiona con el mundo.
    Se mueve cambiando su velocity según la fuerza calculada por la mano.
    """
    body = pymunk.Body()
    body.position = pos

    shape = pymunk.Circle(body, radius)
    shape.mass = mass
    shape.friction = friction
    shape.elasticity = 0.0
    shape.color = PLAYER_COLOR
    shape.collision_type = COLLTYPE_PLAYER

    space.add(body, shape)
    return shape


def add_key(space, pos, radius=12):
    """
    Llave: círculo estático que NO bloquea al jugador (sensor=True).
    Se "recoge" en el callback de colisión: se elimina del Space y se incrementa contador.
    """
    body = pymunk.Body(body_type=pymunk.Body.STATIC)
    body.position = pos

    shape = pymunk.Circle(body, radius)
    shape.sensor = True               # Sensor: detecta pero no hace colisión física
    shape.color = KEY_COLOR
    shape.collision_type = COLLTYPE_KEY

    space.add(body, shape)
    return shape


def add_exit_door(space, pos, radius=18):
    """
    Salida final: también sensor.
    Al tocarla con 3 llaves, se marca game_won=True.
    """
    body = pymunk.Body(body_type=pymunk.Body.STATIC)
    body.position = pos

    shape = pymunk.Circle(body, radius)
    shape.sensor = True
    shape.color = EXIT_DOOR_COLOR
    shape.collision_type = COLLTYPE_EXIT

    space.add(body, shape)
    return shape


def main():
    # PYGAME INIT 
    pygame.init()
    W, H = 750, 750
    screen = pygame.display.set_mode((W, H))

    # Overlay semitransparente para que el texto de Game Over/Win se lea bien
    overlay = pygame.Surface((W, H), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 170))  # negro con alpha

    pygame.display.set_caption("Laberinto - Control por Mano")
    clock = pygame.time.Clock()

    # PYMUNK WORLD 
    space = pymunk.Space()
    space.gravity = (0.0, 0.0)    # top-down: sin gravedad
    space.damping = 0.8           # “rozamiento” global (reduce velocidad con el tiempo)

    # Construcción del laberinto
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
        ((175, 100), (175, 490)),
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

    # Puertas con bisagra 
    door_segments = [
        ((550, 740), (550, 660)),
        ((740, 150), (660, 150)),
        ((100, 240), (100, 185)),
        ((100, 740), (100, 660)),
    ]
    for p1, p2 in door_segments:
        add_door(space, p1, p2, thickness=5, mass=5, max_angle_degrees=90)

    # Elementos del juego
    add_obstacle_ball(space, pos=(400, 300), radius=43, mass=10)
    player = add_player(space, pos=(50, 700), radius=20, mass=3)

    # Llaves y salida
    add_key(space, (50, 50))
    add_key(space, (600, 100))
    add_key(space, (700, 500))
    add_exit_door(space, (400, 100), radius=18)

    # GAME STATE
    collected = 0
    game_won = False
    game_over = False

    # COLLISION CALLBACKS
    def on_player_key(arbiter, _space, _data):
        """Player toca una llave -> se elimina y aumenta contador."""
        nonlocal collected
        if game_over or game_won:
            return False

        s1, s2 = arbiter.shapes
        key_shape = s1 if s1.collision_type == COLLTYPE_KEY else s2

        if key_shape in _space.shapes:
            _space.remove(key_shape, key_shape.body)
            collected += 1

        return False  # Sensor: no hay resolución física

    def on_player_exit(arbiter, _space, _data):
        """Player toca la salida -> si tiene 3 llaves, gana."""
        nonlocal game_won
        if game_over or game_won:
            return False

        if collected >= 3:
            game_won = True
        return False

    def on_player_wall(arbiter, _space, _data):
        """Player toca una pared -> game over."""
        nonlocal game_over
        if game_over or game_won:
            return True

        game_over = True
        return True

    # Registro de colisiones (API moderna de Pymunk)
    space.on_collision(COLLTYPE_PLAYER, COLLTYPE_KEY, begin=on_player_key)
    space.on_collision(COLLTYPE_PLAYER, COLLTYPE_EXIT, begin=on_player_exit)
    space.on_collision(COLLTYPE_PLAYER, COLLTYPE_WALL, begin=on_player_wall)

    # Dibujo “debug” de Pymunk (pinta shapes automáticamente)
    draw_options = pymunk.pygame_util.DrawOptions(screen)

    # Fuentes para HUD / pantallas de estado
    font = pygame.font.SysFont(None, 28)
    big_font = pygame.font.SysFont(None, 60)

    # Guardamos spawn para reiniciar
    SPAWN_POS = (50, 700)

    def reset_game():
        """
        Reinicio "duro": recrea el Space completo para evitar limpiar shapes a mano.
        Mantiene la misma lógica y re-registra colisiones.
        """
        nonlocal collected, game_won, game_over, player, space

        collected = 0
        game_won = False
        game_over = False

        space2 = pymunk.Space()
        space2.gravity = (0.0, 0.0)
        space2.damping = 0.8

        add_outer_walls(space2, W, H, thickness=5, margin=0)
        add_wall_segments(space2, inner_segments, thickness=5)

        for p1, p2 in door_segments:
            add_door(space2, p1, p2, thickness=5, mass=5, max_angle_degrees=90)

        add_obstacle_ball(space2, pos=(400, 300), radius=43, mass=10)
        player = add_player(space2, pos=SPAWN_POS, radius=20, mass=3)

        add_key(space2, (50, 50))
        add_key(space2, (600, 100))
        add_key(space2, (700, 500))
        add_exit_door(space2, (400, 100), radius=18)

        space2.on_collision(COLLTYPE_PLAYER, COLLTYPE_KEY, begin=on_player_key)
        space2.on_collision(COLLTYPE_PLAYER, COLLTYPE_EXIT, begin=on_player_exit)
        space2.on_collision(COLLTYPE_PLAYER, COLLTYPE_WALL, begin=on_player_wall)

        space = space2
        return space

    # CAMARA + MEDIAPIPE INIT 
    cap = cv2.VideoCapture(0)

    # Reutilizamos clases/config del módulo (así mantienes todo centralizado)
    BaseOptions = hand_module.BaseOptions
    HandLandmarker = hand_module.HandLandmarker
    HandLandmarkerOptions = hand_module.HandLandmarkerOptions
    VisionRunningMode = hand_module.VisionRunningMode

    # Crear detector: LIVE_STREAM usa callback (hand_module.get_result)
    options = HandLandmarkerOptions(
        base_options=BaseOptions(model_asset_path='hand_landmarker.task'),
        running_mode=VisionRunningMode.LIVE_STREAM,
        num_hands=1,
        result_callback=hand_module.get_result
    )
    hand_detector = HandLandmarker.create_from_options(options)

    show_camera_window = True

    import time
    start_time = time.time()

    # GAME LOOP 
    while True:
        # Eventos de Pygame (salir / reset)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                cap.release()
                cv2.destroyAllWindows()
                hand_detector.close()
                sys.exit(0)
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    cap.release()
                    cv2.destroyAllWindows()
                    hand_detector.close()
                    sys.exit(0)
                if event.key == pygame.K_r and game_over:
                    space = reset_game()

        # Captura + detección de mano
        ret, frame = cap.read()
        if ret:
            frame = cv2.flip(frame, 1)  # espejo
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            # MediaPipe Image
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)

            # Timestamp para detect_async
            timestamp_ms = int((time.time() - start_time) * 1000)

            # Detectar mano (resultado llega al callback en hand_module.get_result)
            hand_detector.detect_async(mp_image, timestamp_ms)

            # Convertir mano -> velocidad del jugador (solo si seguimos jugando)
            if not game_won and not game_over:
                fx, fy = hand_module.get_player_force()
                player.body.velocity = (fx, fy)

            # Ventana de depuración (OpenCV): landmarks + vector de fuerza
            if show_camera_window:
                annotated_frame = hand_module.draw_landmarks_on_image(
                    rgb_frame, hand_module.detection_result
                )
                annotated_frame_bgr = cv2.cvtColor(annotated_frame, cv2.COLOR_RGB2BGR)

                height, width, _ = annotated_frame_bgr.shape
                center_x, center_y = width // 2, height // 2
                cv2.circle(annotated_frame_bgr, (center_x, center_y), 5, (0, 255, 0), -1)

                fx, fy = hand_module.get_player_force()
                vector_scale = 50
                end_x = int(center_x + fx * vector_scale)
                end_y = int(center_y + fy * vector_scale)

                cv2.arrowedLine(annotated_frame_bgr, (center_x, center_y), (end_x, end_y), (0, 0, 255), 2)

                force_text = f"Fuerza: ({fx:.2f}, {fy:.2f})"
                cv2.putText(annotated_frame_bgr, force_text, (10, 30),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)

                instruction_text = "Mueve tu mano para controlar al jugador"
                cv2.putText(annotated_frame_bgr, instruction_text, (10, height - 20),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

                cv2.imshow('Control por Mano', annotated_frame_bgr)

                if cv2.waitKey(1) & 0xFF == ord('q'):
                    cap.release()
                    cv2.destroyAllWindows()
                    hand_detector.close()
                    sys.exit(0)

        # Dibujo del juego (Pygame)
        screen.fill((255, 255, 255))
        space.debug_draw(draw_options)

        # HUD: llaves
        hud = font.render(f"Llaves: {collected}/3", True, (0, 0, 0))
        screen.blit(hud, (120, 10))

        # Texto de ayuda
        control_text = font.render("Control: Mueve el dedo índice frente a la cámara", True, (0, 0, 0))
        screen.blit(control_text, (W // 2 - control_text.get_width() // 2, H - 50))

        # Pantalla WIN
        if game_won:
            screen.blit(overlay, (0, 0))
            win = big_font.render("¡HAS GANADO!", True, (255, 255, 255))
            screen.blit(win, (W // 2 - win.get_width() // 2, H // 2 - 60))
            tip = font.render("ESC para salir", True, (255, 255, 255))
            screen.blit(tip, (W // 2 - tip.get_width() // 2, H // 2 + 10))

        # Pantalla GAME OVER
        if game_over:
            screen.blit(overlay, (0, 0))
            over = big_font.render("GAME OVER", True, (255, 255, 255))
            screen.blit(over, (W // 2 - over.get_width() // 2, H // 2 - 60))
            tip = font.render("Pulsa R para intentarlo otra vez", True, (255, 255, 255))
            screen.blit(tip, (W // 2 - tip.get_width() // 2, H // 2 + 10))

        # Física: substeps para estabilidad
        DT = 1 / 50.0
        SUBSTEPS = 5
        for _ in range(SUBSTEPS):
            space.step(DT / SUBSTEPS)

        #  Flip / FPS 
        pygame.display.flip()
        clock.tick(50)


if __name__ == "__main__":
    main()
