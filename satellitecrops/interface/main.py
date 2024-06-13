import numpy as np
import tensorflow as tf
from colorama import Fore, Style

from sklearn.model_selection import train_test_split
from tensorflow.keras.optimizers import Adam

from satellitecrops.params import *
from satellitecrops.model.unet import unet, train_model
from satellitecrops.registry import save_model, save_results
from satellitecrops.data import create_Xy
from satellitecrops.preproc import scaling


def train(
        path:str,
        learning_rate:float=0.0005,
        batch_size:int= 16,
        patience:int= 5,
        alpha:float=0.25,
        gamma:float=2
    ) -> float:

    """
    - Create X and y arrays from the BQ path
    - Train on the preprocessed dataset
    - Store training results and model weights

    Return val_meanIoU as a float
    """

    print(Fore.MAGENTA + "\n⭐️ Use case: train" + Style.RESET_ALL)
    print(Fore.BLUE + "\nLoading preprocessed validation data..." + Style.RESET_ALL)

    # Create train and test set
    X , y = create_Xy(path)
    y_cat = tf.keras.utils.to_categorical(y)
    X_scaled = scaling(X, 3)
    X_train, X_test, y_train, y_test = train_test_split(X_scaled, y_cat, test_size=0.2)

    n_classes = len(y)
    img_height = y.shape[1]
    img_width = y.shape[2]
    channels = X.shape[-1] # Attention bien vérifier que c'est la bonne shape une fois X créé

    # Train a model on the training set, using `model.py`
    model = None

    optimizer = Adam(learning_rate=learning_rate)

    model = unet(n_classes=n_classes,
                 img_height=img_height,
                 img_width=img_width,
                 optimizer=optimizer,
                 alpha=alpha,
                 gamma=gamma)

    model, history = train_model(
        model,
        X_train,
        y_train,
        batch_size=batch_size,
        patience=patience,
        validation_data=(X_test, y_test)
    )

    val_meanIoU = np.max(history.history['val_meanIoU'])

    params = dict(
        context="train",
        training_set_size=X_train.shape[0],
        row_count=len(X_train), #To be changed
    )

    # Save results on the hard drive using taxifare.ml_logic.registry
    save_results(params=params, metrics=dict(mae=val_meanIoU))

    # Save model weight on the hard drive (and optionally on GCS too!)
    save_model(model=model)

    print("✅ train() done \n")

    return val_meanIoU





if __name__ == '__main__':
    #preprocess()
    train("./data/departments/landes/eopatches")
    #evaluate()
    #pred()
