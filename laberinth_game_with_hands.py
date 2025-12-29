import sys
import pygame
import pymunk
import pymunk.pygame_util
import mediapipe as mp
import cv2
import numpy as np

# Importar las funciones necesarias de tu módulo
import hand_force_application as hand_module

WALL_COLOR = (200, 50, 50, 255)         # rojo
INNER_WALL_COLOR = (50, 50, 200, 255)   # azul
OBSTACLE_COLOR = (0, 150, 0, 255)       # verde
DOOR_COLOR = (50, 50, 200, 255)         # azul (puertas con bisagra)
PLAYER_COLOR = (0, 0, 0, 255)           # negro

KEY_COLOR = (240, 200, 0, 255)          # amarillo
EXIT_DOOR_COLOR = (255, 140, 0, 255)    # naranja


# --- collision types (para detectar contactos) ---
COLLTYPE_PLAYER = 1
COLLTYPE_KEY = 2
COLLTYPE_EXIT = 3
COLLTYPE_WALL = 4  


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
        w.collision_type = COLLTYPE_WALL  

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
        s.collision_type = COLLTYPE_WALL  
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
    body = pymunk.Body(body_type=pymunk.Body.STATIC)
    body.position = pos

    shape = pymunk.Circle(body, radius)
    shape.sensor = True
    shape.color = KEY_COLOR
    shape.collision_type = COLLTYPE_KEY

    space.add(body, shape)
    return shape


def add_exit_door(space, pos, radius=18):
    body = pymunk.Body(body_type=pymunk.Body.STATIC)
    body.position = pos

    shape = pymunk.Circle(body, radius)
    shape.sensor = True
    shape.color = EXIT_DOOR_COLOR
    shape.collision_type = COLLTYPE_EXIT

    space.add(body, shape)
    return shape


def main():
    pygame.init()
    W, H = 750, 750
    screen = pygame.display.set_mode((W, H))
    # Overlay semitransparente para GAME OVER / WIN
    overlay = pygame.Surface((W, H), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 170))  # negro con alpha (0-255)

    pygame.display.set_caption("Laberinto - Control por Mano")
    clock = pygame.time.Clock()

    space = pymunk.Space()
    space.gravity = (0.0, 0.0)
    space.damping = 0.8

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

    # Puertas con bisagra existentes (NO cuentan como pared mortal)
    door_segments = [
        ((550, 740), (550, 660)),
        ((740, 150), (660, 150)),
        ((100, 240), (100, 185)),
        ((100, 740), (100, 660)),
    ]
    for p1, p2 in door_segments:
        add_door(space, p1, p2, thickness=5, mass=5, max_angle_degrees=90)

    add_obstacle_ball(space, pos=(400, 300), radius=43, mass=10)

    player = add_player(space, pos=(50, 700), radius=20, mass=3)

    add_key(space, (50, 50))
    add_key(space, (600, 100))
    add_key(space, (700, 500))

    add_exit_door(space, (400, 100), radius=18)

    collected = 0
    game_won = False
    game_over = False

    # --- colisiones ---
    def on_player_key(arbiter, _space, _data):
        nonlocal collected
        if game_over or game_won:
            return False
        s1, s2 = arbiter.shapes
        key_shape = s1 if s1.collision_type == COLLTYPE_KEY else s2
        if key_shape in _space.shapes:
            _space.remove(key_shape, key_shape.body)
            collected += 1
        return False

    def on_player_exit(arbiter, _space, _data):
        nonlocal game_won
        if game_over or game_won:
            return False
        if collected >= 3:
            game_won = True
        return False

    def on_player_wall(arbiter, _space, _data):
        nonlocal game_over
        if game_over or game_won:
            return True
        game_over = True
        return True  # dejamos que la física resuelva el choque, pero ya marcamos game over

    space.on_collision(COLLTYPE_PLAYER, COLLTYPE_KEY, begin=on_player_key)
    space.on_collision(COLLTYPE_PLAYER, COLLTYPE_EXIT, begin=on_player_exit)
    space.on_collision(COLLTYPE_PLAYER, COLLTYPE_WALL, begin=on_player_wall)

    draw_options = pymunk.pygame_util.DrawOptions(screen)

    font = pygame.font.SysFont(None, 28)
    big_font = pygame.font.SysFont(None, 60)

    SPEED = 150

    # Guardamos spawn para reiniciar
    SPAWN_POS = (50, 700)

    def reset_game():
        nonlocal collected, game_won, game_over, player, space
        # Para un reset limpio y simple: reiniciamos el proceso llamando main otra vez
        # pero como no queremos salir, hacemos un "hard reset" recreando el Space.
        collected = 0
        game_won = False
        game_over = False

        # Re-crear el espacio completo (más fácil que eliminar cosas una por una)
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

        # Re-registrar colisiones con las nuevas referencias (y el nuevo space)
        space2.on_collision(COLLTYPE_PLAYER, COLLTYPE_KEY, begin=on_player_key)
        space2.on_collision(COLLTYPE_PLAYER, COLLTYPE_EXIT, begin=on_player_exit)
        space2.on_collision(COLLTYPE_PLAYER, COLLTYPE_WALL, begin=on_player_wall)

        space = space2
        return space

    # Inicializar la cámara y MediaPipe usando el módulo existente
    cap = cv2.VideoCapture(0)
    
    # Inicializar el detector de MediaPipe usando la configuración de tu módulo
    BaseOptions = hand_module.BaseOptions
    HandLandmarker = hand_module.HandLandmarker
    HandLandmarkerOptions = hand_module.HandLandmarkerOptions
    VisionRunningMode = hand_module.VisionRunningMode
    
    # Crear el detector de manos
    options = HandLandmarkerOptions(
        base_options=BaseOptions(model_asset_path='hand_landmarker.task'),
        running_mode=VisionRunningMode.LIVE_STREAM,
        num_hands=1,
        result_callback=hand_module.get_result
    )
    
    hand_detector = HandLandmarker.create_from_options(options)
    
    # Variables para controlar la ventana de la cámara
    show_camera_window = True
    
    # Tiempo para el timestamp
    import time
    start_time = time.time()

    while True:
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
                if event.key == pygame.K_c:  # Tecla C para alternar la ventana de la cámara
                    show_camera_window = not show_camera_window

        # Capturar y procesar frame de la cámara
        ret, frame = cap.read()
        if ret:
            # Voltear horizontalmente para efecto espejo
            frame = cv2.flip(frame, 1)
            # Convertir a RGB
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            # Crear objeto MediaPipe Image
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
            # Calcular timestamp
            timestamp_ms = int((time.time() - start_time) * 1000)
            # Detectar mano 
            hand_detector.detect_async(mp_image, timestamp_ms)
            # Obtener fuerza del movimiento de la mano
            if not game_won and not game_over:
                fx, fy = hand_module.get_player_force()
                player.body.velocity = (fx, fy)
            
            # Mostrar ventana de la cámara con landmarks
            if show_camera_window:
                # Dibujar landmarks en la imagen
                annotated_frame = hand_module.draw_landmarks_on_image(rgb_frame, hand_module.detection_result)
                # Convertir de vuelta a BGR para mostrar con OpenCV
                annotated_frame_bgr = cv2.cvtColor(annotated_frame, cv2.COLOR_RGB2BGR)
                
                # Obtener dimensiones de la imagen para el centro
                height, width, _ = annotated_frame_bgr.shape
                
                # Dibujar el centro de la pantalla
                center_x, center_y = width // 2, height // 2
                cv2.circle(annotated_frame_bgr, (center_x, center_y), 5, (0, 255, 0), -1)
                
                # Obtener fuerza del jugador
                fx, fy = hand_module.get_player_force()
                
                # Dibujar vector de fuerza (escalado para mejor visualización)
                force_scale = 50  # Ajusta este valor para hacer el vector más visible
                end_x = int(center_x + fx * force_scale)
                end_y = int(center_y + fy * force_scale)
                
                # Dibujar línea de fuerza
                cv2.arrowedLine(annotated_frame_bgr, (center_x, center_y), (end_x, end_y), (0, 0, 255), 2)
                
                # Mostrar valores de fuerza como texto
                force_text = f"Fuerza: ({fx:.2f}, {fy:.2f})"
                cv2.putText(annotated_frame_bgr, force_text, (10, 30), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
                
                # Mostrar instrucciones
                instruction_text = "Mueve tu mano para controlar al jugador"
                cv2.putText(annotated_frame_bgr, instruction_text, (10, height - 20),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

                # Mostrar frame
                cv2.imshow('Control por Mano', annotated_frame_bgr)
                
                # Salir si se presiona 'q' en la ventana de OpenCV
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    cap.release()
                    cv2.destroyAllWindows()
                    hand_detector.close()
                    sys.exit(0)

        screen.fill((255, 255, 255))
        space.debug_draw(draw_options)

        hud = font.render(f"Llaves: {collected}/3", True, (0, 0, 0))
        screen.blit(hud, (120, 10))

        # Instrucciones para el control
        control_text = font.render("Control: Mueve el dedo índice frente a la cámara", True, (0, 0, 0))
        screen.blit(control_text, (W//2 - control_text.get_width()//2, H - 50))
        
        camera_text = font.render("Presiona 'C' para mostrar/ocultar cámara | 'Q' en ventana cámara para salir", True, (0, 0, 0))
        screen.blit(camera_text, (W//2 - camera_text.get_width()//2, H - 20))

        if game_won:
          screen.blit(overlay, (0, 0))

          win = big_font.render("¡HAS GANADO!", True, (255, 255, 255))
          screen.blit(win, (W//2 - win.get_width()//2, H//2 - 60))

          tip = font.render("ESC para salir", True, (255, 255, 255))
          screen.blit(tip, (W//2 - tip.get_width()//2, H//2 + 10))

        if game_over:
          screen.blit(overlay, (0, 0))

          over = big_font.render("GAME OVER", True, (255, 255, 255))
          screen.blit(over, (W//2 - over.get_width()//2, H//2 - 60))

          tip = font.render("Pulsa R para intentarlo otra vez", True, (255, 255, 255))
          screen.blit(tip, (W//2 - tip.get_width()//2, H//2 + 10))

        DT = 1 / 50.0
        SUBSTEPS = 5
        for _ in range(SUBSTEPS):
            space.step(DT / SUBSTEPS)

        pygame.display.flip()
        clock.tick(50)

    cap.release()
    cv2.destroyAllWindows()
    hand_detector.close()


if __name__ == "__main__":
    main()