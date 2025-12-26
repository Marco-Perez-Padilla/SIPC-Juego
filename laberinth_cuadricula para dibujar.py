import sys
import pygame
import pymunk


# ---------- CONFIGURACIÓN ----------
WIDTH, HEIGHT = 750, 750
CELL_SIZE = 50  # tamaño de cada cuadrado

GRID_COLOR = (220, 220, 220)
TEXT_COLOR = (120, 120, 120)
BG_COLOR = (255, 255, 255)


def draw_grid(screen, font):
    """Dibuja una rejilla con coordenadas"""
    # Líneas verticales
    for x in range(0, WIDTH + 1, CELL_SIZE):
        pygame.draw.line(screen, GRID_COLOR, (x, 0), (x, HEIGHT), 1)
        label = font.render(str(x), True, TEXT_COLOR)
        screen.blit(label, (x + 2, 2))

    # Líneas horizontales
    for y in range(0, HEIGHT + 1, CELL_SIZE):
        pygame.draw.line(screen, GRID_COLOR, (0, y), (WIDTH, y), 1)
        label = font.render(str(y), True, TEXT_COLOR)
        screen.blit(label, (2, y + 2))


def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Grid para diseñar el laberinto")
    clock = pygame.time.Clock()

    font = pygame.font.SysFont(None, 18)

    # 🔹 Pymunk sigue aquí por coherencia, pero no usamos física todavía
    space = pymunk.Space()
    space.gravity = (0, 0)

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sys.exit()
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                sys.exit()

        screen.fill(BG_COLOR)

        # 🔹 Solo el grid visual
        draw_grid(screen, font)

        pygame.display.flip()
        clock.tick(60)


if __name__ == "__main__":
    main()
