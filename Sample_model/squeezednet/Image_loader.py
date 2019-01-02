"""
AUTHOR: bulletcross@gmail.com (Vishal Keshav)
TITLE : Image loader utility for fetching train/test data
"""
from keras.datasets import mnist, fashion_mnist, cifar10, cifar100
from keras.utils import to_categorical
from keras.preprocessing import image
from PIL import Image
import numpy as np
import os
from tqdm import tqdm
import h5py

def load_data_simple(dataset_name):
    if dataset_name == 'mnist':
        (x_train, y_train), (x_test, y_test) = mnist.load_data()
    elif dataset_name == 'fashion_mnist':
        (x_train, y_train), (x_test, y_test) = fashion_mnist.load_data()
    elif dataset_name == 'cifar10':
        (x_train, y_train), (x_test, y_test) = cifar10.load_data()
    elif dataset_name == 'cifar100':
        (x_train, y_train), (x_test, y_test) = cifar100.load_data(label_mode='fine')
    else:
        print("Dataset " + dataset_name + " not found, defaulting to mnist.")
        (x_train, y_train), (x_test, y_test) = mnist.load_data()
    if(dataset_name == 'cifar10' or dataset_name == 'cifar100'):
        x_train = x_train.reshape(x_train.shape[0], 32, 32, 3)
        x_test = x_test.reshape(x_test.shape[0], 32, 32, 3)
        if dataset_name == 'cifar10':
            y_train = to_categorical(y_train, 10)
            y_test = to_categorical(y_test, 10)
        else:
            y_train = to_categorical(y_train, 100)
            y_test = to_categorical(y_test, 100)
    elif dataset_name == 'mnist' or dataset_name == 'fashion_mnist':
        x_train = x_train.reshape(x_train.shape[0], 28, 28, 1)
        x_test = x_test.reshape(x_test.shape[0], 28, 28, 1)
        y_train = to_categorical(y_train, 10)
        y_test = to_categorical(y_test, 10)
    else:
        x_train = x_train.reshape(x_train.shape[0], 28, 28, 1)
        x_test = x_test.reshape(x_test.shape[0], 28, 28, 1)
        y_train = to_categorical(y_train, 10)
        y_test = to_categorical(y_test, 10)
    x_train = x_train.astype('float32')
    x_test = x_test.astype('float32')
    x_train = x_train/225
    t_test = x_test/225
    return (x_train, y_train), (x_test, y_test)

def load_data_external(dataset_name, path):
    x_train = np.zeros([200*500, 64, 64, 3], dtype='uint8')
    y_train = np.zeros([200*500], dtype='uint8')
    x_test = np.zeros([200*50, 64, 64, 3], dtype='uint8')
    y_test = np.zeros([200*50], dtype='uint8')
    train_path = path+'/train'
    image_index = 0
    class_index = 0
    label_map = {}
    for class_folder in tqdm(os.listdir(train_path)):
        class_image_dir = os.path.join(os.path.join(train_path, class_folder), 'images')
        label_map[class_folder] = class_index
        for image_file in os.listdir(class_image_dir):
            image_blob = Image.open(os.path.join(class_image_dir, image_file))
            #If image is black-white (one channel)
            image_array = np.array(image_blob.getdata())
            if image_array.size == 64*64:
                image_array = image_array.reshape(image_blob.size[0], image_blob.size[1])
                image_array = np.array([image_array, image_array, image_array]).reshape(image_blob.size[0], image_blob.size[1], 3)
            else:
                image_array = image_array.reshape(image_blob.size[0], image_blob.size[1], 3)
            x_train[image_index] = image_array
            y_train[image_index] = class_index
            image_index = image_index + 1
        class_index = class_index + 1
        if class_index >= 200:
            break
    #Reading validation data as test data
    val_data_path = path+'/val/val_annotations.txt'
    val_data_file = open(val_data_path, 'r')
    val_data_content = val_data_file.read()

    test_label_map = {}
    for line in val_data_content.splitlines():
        words = line.strip().split()
        test_label_map[words[0]] = words[1]

    test_path = path+'/val/images'
    image_index = 0
    for image_file in tqdm(os.listdir(test_path)):
        if test_label_map[image_file] in label_map.keys():
            image_blob = Image.open(os.path.join(test_path, image_file))
            image_array = np.array(image_blob.getdata())
            if image_array.size == 64*64:
                image_array = image_array.reshape(image_blob.size[0], image_blob.size[1])
                image_array = np.array([image_array, image_array, image_array]).reshape(image_blob.size[0], image_blob.size[1], 3)
            else:
                image_array = image_array.reshape(image_blob.size[0], image_blob.size[1], 3)
            x_test[image_index] = image_array
            y_test[image_index] = label_map[test_label_map[image_file]]
            image_index = image_index + 1
        else:
            pass
    #Normalize the data and make y categorical
    x_train = x_train.astype('float32')
    x_test = x_test.astype('float32')
    x_train = x_train/225
    x_test = x_test/225
    y_train = to_categorical(y_train, 200)
    y_test = to_categorical(y_test, 200)
    permute_train = np.random.permutation(x_train.shape[0])
    permute_test = np.random.permutation(x_test.shape[0])
    x_train = x_train[permute_train]
    y_train = y_train[permute_train]
    x_test = x_test[permute_test]
    y_test = y_test[permute_test]
    #All read done, save h5py data before returning
    data_file = h5py.File('tiny_imagenet.h5', 'w')
    group_data = data_file.create_group('tiny_imagenet_group')
    group_data.create_dataset('x_train', data=x_train, compression="gzip", compression_opts=2)
    group_data.create_dataset('y_train', data=y_train, compression="gzip", compression_opts=2)
    group_data.create_dataset('x_test', data=x_test, compression="gzip", compression_opts=2)
    group_data.create_dataset('y_test', data=y_test, compression="gzip", compression_opts=2)
    data_file.close()
    return (x_train, y_train), (x_test, y_test)

def load_data_caltech(dataset_name, path):
    directory_name_list = [x for x in os.walk(path)][0][1]
    label_map = {class_index: class_name for class_index, class_name in enumerate(directory_name_list)}
    x_train_array = []
    y_train_array = []
    x_test_array = []
    y_test_array = []
    for class_index, class_name in label_map.iteritems():
        class_path = os.path.join(path, class_name)
        image_file_path_list = [os.path.join(class_path, f) for f in os.listdir(class_path)]
        temp_image_array = []
        for image_file_path in image_file_path_list:
            image_blob = image.load_img(path = image_file_path, grayscale = False, target_size = (224, 224))
            temp_image_array.append(image.img_to_array(image_blob))
        split = int(np.floor(len(temp_image_array)*0.95))
        x_train_array.append(np.stack(temp_image_array[:split], axis=0))
        x_test_array.append(np.stack(temp_image_array[split:], axis=0))
        y_train_array.append(np.full(shape = (len(temp_image_array[:split])), fill_value = class_index))
        y_test_array.append(np.full(shape = (len(temp_image_array[split:])),fill_value = class_index))
    x_train = np.concatenate(x_train_array)
    y_train = to_categorical(np.concatenate(y_train_array), 102)
    x_test = np.concatenate(x_test_array)
    y_test = to_categorical(np.concatenate(y_test_array), 102)
    x_train = x_train.astype('float32')
    x_test = x_test.astype('float32')
    x_train = x_train/225
    x_test = x_test/225
    permute_train = np.random.permutation(x_train.shape[0])
    permute_test = np.random.permutation(x_test.shape[0])
    x_train = x_train[permute_train]
    y_train = y_train[permute_train]
    x_test = x_test[permute_test]
    y_test = y_test[permute_test]
    data_file = h5py.File('../caltech101.h5', 'w')
    group_data = data_file.create_group('caltech101_group')
    group_data.create_dataset('x_train', data=x_train, compression="gzip", compression_opts=2)
    group_data.create_dataset('y_train', data=y_train, compression="gzip", compression_opts=2)
    group_data.create_dataset('x_test', data=x_test, compression="gzip", compression_opts=2)
    group_data.create_dataset('y_test', data=y_test, compression="gzip", compression_opts=2)
    data_file.close()
    return (x_train, y_train), (x_test, y_test)