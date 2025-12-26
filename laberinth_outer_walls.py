import sys, random
random.seed(1) # make the simulation the same each time, easier to debug
import pygame
import pymunk
import pymunk.pygame_util

def add_outer_walls(space, width, height, thickness=5, margin=10):
    """
    Crea 4 paredes estáticas (rectángulo) dentro de la ventana.
    margin: separación respecto al borde de la pantalla para que no quede pegado.
    """
    body = space.static_body

    left = margin
    right = width - margin
    top = margin
    bottom = height - margin

    walls = [
        pymunk.Segment(body, (left, top), (right, top), thickness),        # arriba
        pymunk.Segment(body, (left, bottom), (right, bottom), thickness),  # abajo
        pymunk.Segment(body, (left, top), (left, bottom), thickness),      # izquierda
        pymunk.Segment(body, (right, top), (right, bottom), thickness),    # derecha
    ]

    for w in walls:
        w.friction = 1.0
        w.elasticity = 0.0  # 0 = sin rebote
        w.color = (200, 50, 50, 255)  # ROJO (R,G,B,A)

    space.add(*walls)
    return walls


def main():
  pygame.init()

  W, H = 750, 750
  screen = pygame.display.set_mode((W, H))
  pygame.display.set_caption("Laberinto - paredes exteriores")
  clock = pygame.time.Clock()

  space = pymunk.Space()
  space.gravity = (0.0, 0.0)  # top-down (sin gravedad)

  add_outer_walls(space, W, H, thickness=5, margin=0)

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
