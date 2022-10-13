import os
import numpy as np
import cv2

class BVLC:
    def __init__(self, channel_merge = False, stride = 1, n_Octaves = 3, epsilon = 0.000001, pairs = ((0, 1), (1, 0), (1, 1), (1, -1))) -> None:
        self.block_size = 2
        self.patch_area = self.block_size ** 2
        self.channel_merge = channel_merge
        self.pairs = pairs
        self.stride = stride
        self.epsilon = epsilon

    def padding(self, img : np.array):
        padding_size = [0, 0, 0, 0] # up down left right
        if img.shape[0] % self.block_size == 0:
            padding_size[0], padding_size[1] = 1, 1
        elif img.shape[0] % self.block_size == 1:
            padding_size[0] = 1
        if img.shape[1] % self.block_size == 0:
            padding_size[2], padding_size[3] = 1, 1
        return padding_size

    def add_padding(self, gray : np.array, padding_size : tuple):
        up_pad = np.zeros((padding_size[0], gray.shape[1]))
        down_pad = np.zeros((padding_size[1], gray.shape[1]))
        left_pad = np.zeros((gray.shape[0] + padding_size[0] + padding_size[1], padding_size[2]))
        right_pad = np.zeros((gray.shape[0] + padding_size[0] + padding_size[1], padding_size[3]))  
        up_cat_pad = np.concatenate((up_pad, gray), axis = 0)
        down_cat_pad = np.concatenate((up_cat_pad, down_pad), axis = 0)
        left_cat_pad = np.concatenate((left_pad, down_cat_pad), axis = 1)
        right_cat_pad = np.concatenate((left_cat_pad, right_pad), axis = 1)
        return right_cat_pad

    def local_coree_coef(self, current_block : np.array, shift_block : np.array):
        local_mean = np.mean(current_block)
        local_std = np.std(current_block)
        shift_mean = np.mean(shift_block)
        shift_std = np.std(shift_block)

        # intensity_changes = np.array([current_block * shift_block[0, 0], 
        #                                 current_block * shift_block[0, 1], current_block * shift_block[1, 0],
        #                                 current_block * shift_block[1, 1]])
        

        nominator = np.sum(current_block*shift_block)/self.patch_area - local_mean*shift_mean
        dominator = local_std * shift_std + self.epsilon

        return nominator/dominator

    def extract(self, img : np.array, gray = "grayscale", path = None):
        if gray == "grayscale":
            img_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        elif gray == "avg":
            img_gray = (img[:, :, 0] + img[:, :, 1] + img[:, :, 2])/3

        padding_size = self.padding(img_gray)

        padd_gray = self.add_padding(img_gray, padding_size)

        row_index, col_index = padd_gray.shape[0], padd_gray.shape[1]

        row_block_index, col_block_index = int((row_index - 1)/self.block_size), int((col_index - 1)/self.block_size)

        output = np.zeros((row_block_index, col_block_index))

        for i in range(self.stride, row_index - self.stride, self.block_size):
            for j in range(self.stride, col_index - self.stride, self.block_size):
                current_index = (int(i/self.block_size), int(j/self.block_size))
                current_block = padd_gray[i:i+self.block_size, j:j+self.block_size]
                local_coefs = []
                for x in self.pairs:
                    i_shift = i + x[1]
                    j_shift = j + x[0]
                    shift_block = padd_gray[i_shift : i_shift + self.block_size, j_shift : j_shift + self.block_size]
                    local_coefs.append(self.local_coree_coef(current_block, shift_block))
                output[current_index[0], current_index[1]] = max(local_coefs) - min(local_coefs)
        cv2.imshow("results", output)
        cv2.waitKey(0)
        print(np.unique(output))
        if path:
            frame_normed = 255 * (output - output.min()) / (output.max() - output.min())
            frame_normed = np.array(frame_normed, np.int)
            cv2.imwrite(path, frame_normed)


os.chdir("..")
main_data_dir = os.getcwd() + "\\ExampleImage"
img_path1 = main_data_dir + "\\CHGastro_Abnormal_037.png"
img_path2 = main_data_dir + "\\CHGastro_Normal_047.png"
img1 = cv2.imread(img_path1)
img2 = cv2.imread(img_path2)

bdlc = BVLC()
extract1 = bdlc.extract(img = img1, path="ExampleImage\\BVLC_" + img_path1.split("\\")[-1])                  
extract2 = bdlc.extract(img = img2, path="ExampleImage\\BVLC_" + img_path2.split("\\")[-1])