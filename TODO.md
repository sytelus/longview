* Fix cell size issue
* Refactor _plot* interface to accept all values, for ImagePlot only use last value
* Refactor ImagePlot for arbitrary number of images with alpha, cmap
* Change tw.open -> tw.create_viz
* Make sure streams have names as key, each data point has index
* Add tw.open_viz(stream_name, from_index)_
* Add persist=device_name option for streams
* Ability to use streams in standalone mode
* tw.create_viz on server side
* tw.log for server side
* experiment with IPC channel
* confusion matrix as in https://pytorch.org/tutorials/intermediate/char_rnn_classification_tutorial.html
* Speed up import
* Do linting
* live perf data
* NaN tracing
* PCA
* Remove error if MNIST notebook is on and we run fruits
* Remove 2nd image from fruits

