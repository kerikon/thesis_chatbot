from PIL import Image, ImageOps
import matplotlib.pyplot as plt
import numpy as np
import time


class MapDraw:

    @staticmethod
    def draw_position(pos, dpi):
        map_img = Image.open('images/map.pgm')
        map_img = ImageOps.flip(map_img)

        plt.imshow(map_img, cmap='gray')
        plt.axis('off')

        plt.plot((pos.get('pos_x') + 110) / 0.02, (pos.get('pos_y') + 4) / 0.02, 'bx', markersize=3, mew=0.6)

        plt.gca().invert_yaxis()

        save_img_file = time.strftime('%d.%m.%Y_%H_%M_%S_position.png')

        plt.savefig('../chatbot_interface/chatbot/static/path_images/' + save_img_file, bbox_inches='tight', dpi=dpi)

        plt.close()

        return 'path_images/' + save_img_file

    @staticmethod
    def draw_path(poses, dpi, color):
        map_img = Image.open('images/map.pgm')
        map_img = ImageOps.flip(map_img)

        plt.imshow(map_img, cmap='gray')
        plt.axis('off')

        x = np.array([int((point[1].get('pos_x') + 110) / 0.02) for point in poses])
        y = np.array([int((point[1].get('pos_y') + 4) / 0.02) for point in poses])

        plt.quiver(x[:-1], y[:-1], x[1:] - x[:-1], y[1:] - y[:-1],
                   scale_units='xy', angles='xy', scale=1, color=color)

        plt.gca().invert_yaxis()

        save_img_file = time.strftime('%d.%m.%Y_%H_%M_%S_path.png')

        plt.savefig('../chatbot_interface/chatbot/static/path_images/' + save_img_file, bbox_inches='tight', dpi=dpi)

        plt.close()

        return 'path_images/' + save_img_file
