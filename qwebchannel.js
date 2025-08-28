// qwebchannel.js - Provided by Qt for inter-process communication
// This file is typically found in Qt's installation directory, e.g.,
// C:/Qt/5.15.2/msvc2019_64/qml/QtWebChannel/qwebchannel.js

(function() {
    if (typeof QWebChannel != 'undefined') {
        return;
    }

    QWebChannel = function(transport, initCallback) {
        if (typeof transport !== 'object' || typeof transport.send !== 'function') {
            throw new Error("The QWebChannel expects a valid transport object with a send function.");
        }

        var channel = this;
        this.transport = transport;
        this.send = function(data) {
            if (typeof data !== 'string') {
                data = JSON.stringify(data);
            }
            channel.transport.send(data);
        };

        this.objects = {};
        this.propertyUpdateSignal = {};
        this.signalEmitted = {};

        this.execCallbacks = {};
        this.execId = 0;

        this.exec = function(data, callback) {
            if (!callback) {
                // non-blocking call
                this.send(data);
                return;
            }
            if (this.execId === Number.MAX_SAFE_INTEGER) {
                this.execId = 0;
            }
            var id = ++this.execId;
            this.execCallbacks[id] = callback;
            data.id = id;
            this.send(data);
        };

        this.transport.onmessage = function(message) {
            var data = message.data;
            if (typeof data === 'string') {
                data = JSON.parse(data);
            }
            if (data.type === QWebChannelMessage.Signal) {
                var signalName = data.signal;
                if(signalName && channel.signalEmitted[data.object]) {
                    channel.signalEmitted[data.object][signalName].apply(channel, data.args);
                }
            } else if (data.type === QWebChannelMessage.Response) {
                var callback = channel.execCallbacks[data.id];
                if (callback) {
                    callback(data.data);
                    delete channel.execCallbacks[data.id];
                }
            } else if (data.type === QWebChannelMessage.PropertyUpdate) {
                var object = channel.objects[data.object];
                if (object) {
                    object.unwrapProperties(data.data);
                }
            } else if (data.id) { // unknown response
                var callback = channel.execCallbacks[data.id];
                if (callback) {
                    callback(data.data);
                    delete channel.execCallbacks[data.id];
                }
            }
        };

        this.init = function() {
            var data = {
                type: QWebChannelMessage.Init
            };
            channel.exec(data, function(data) {
                for (var objectName in data) {
                    var object = new QObject(objectName, data[objectName], channel);
                    channel.objects[objectName] = object;
                    // so that we can access the objects from the outside
                    if(!channel[objectName]) {
                        channel[objectName] = object;
                    }
                }

                for (var objectName in channel.objects) {
                    var object = channel.objects[objectName];
                    object.unwrapProperties();
                }

                if (initCallback) {
                    initCallback(channel);
                }
            });
        };

        this.init();
    };

    var QWebChannelMessage = {
        Init: 1,
        Signal: 2,
        PropertyUpdate: 3,
        InvokeMethod: 4,
        Response: 5
    };

    function QObject(name, data, webChannel) {
        this.__id__ = name;
        this.webChannel = webChannel;

        this.unwrapProperties = function(properties) {
            if (!properties) {
                properties = data.properties;
            }
            for (var propertyIdx in properties) {
                var propertyName = properties[propertyIdx];
                var propertyValue = data.properties[propertyName];
                if (propertyValue && propertyValue.__id__) {
                    this[propertyName] = webChannel.objects[propertyValue.__id__];
                } else {
                    this[propertyName] = propertyValue;
                }
            }
        };

        var object = this;
        for (var methodIdx in data.methods) {
            var methodName = data.methods[methodIdx];
            object[methodName] = (function(methodName) {
                return function() {
                    var args = [];
                    var callback;
                    for (var i = 0; i < arguments.length; i++) {
                        if (typeof arguments[i] === 'function') {
                            callback = arguments[i];
                        } else {
                            args.push(arguments[i]);
                        }
                    }

                    webChannel.exec({
                        type: QWebChannelMessage.InvokeMethod,
                        object: object.__id__,
                        method: methodName,
                        args: args
                    }, callback);
                };
            })(methodName);
        }

        webChannel.signalEmitted[name] = {};
        for (var signalIdx in data.signals) {
            var signalName = data.signals[signalIdx];
            webChannel.signalEmitted[name][signalName] = (function() {
                var signal = function() {
                    for (var i = 0; i < signal.length; i++) {
                        signal[i].apply(signal, arguments);
                    }
                };
                signal.connect = function(callback) {
                    if (typeof callback !== 'function') {
                        console.error("Signal.connect: callback is not a function!");
                        return;
                    }
                    signal.push(callback);
                };
                signal.disconnect = function(callback) {
                    for (var i = 0; i < signal.length; i++) {
                        if (signal[i] === callback) {
                            signal.splice(i, 1);
                            return;
                        }
                    }
                };
                return signal;
            })();
            object[signalName] = webChannel.signalEmitted[name][signalName];
        }

        webChannel.propertyUpdateSignal[name] = {};
        for (var propertyIdx in data.properties) {
            var propertyName = data.properties[propertyIdx];
            webChannel.propertyUpdateSignal[name][propertyName] = (function(propertyName) {
                var signal = function(callback) {
                    object[propertyName + "Changed"] = signal;
                    signal.connect = function(callback) {
                        if (typeof callback !== 'function') {
                            console.error("propertyUpdateSignal.connect: callback is not a function!");
                            return;
                        }
                        signal.push(callback);
                    };
                    signal.disconnect = function(callback) {
                        for (var i = 0; i < signal.length; i++) {
                            if (signal[i] === callback) {
                                signal.splice(i, 1);
                                return;
                            }
                        }
                    };
                };
                return signal;
            })(propertyName);
        }
    }
})();