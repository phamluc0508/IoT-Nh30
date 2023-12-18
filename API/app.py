from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import numpy as np
import pandas as pd
import warnings

app = Flask(__name__)
CORS(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:123456@localhost/data_train_iot'
app.config['SECRET_KEY'] = 'my super secret'
CORS(app, origins='*', methods=['GET', 'POST', 'PUT', 'DELETE'])
db = SQLAlchemy(app)

class Datas(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    temperature = db.Column(db.Float, nullable=False)
    humidity = db.Column(db.Float, nullable=False)
    spo = db.Column(db.Float, nullable=False)
    heartbeat = db.Column(db.Float, nullable=False)
    disease = db.Column(db.String(200), nullable=False)

    def __repr__(self):
        return '<Datas %r>' % self.disease
W1PL, b1PL, W2PL, b2PL=0,0,0,0
with app.app_context():
    
    warnings.filterwarnings("ignore", category=DeprecationWarning)

    datas = Datas.query.all()
    data_list = []
    for data in datas:

        data_list.append([data.temperature,data.humidity,data.spo,data.heartbeat,data.disease])


    array_left = [row[:4] for row in data_list]  # Cột từ 0 đến 3
    array_right = [row[4:] for row in data_list]  # Cột 4
    trainingSet=list(array_left)
    # CHUẨN HOÁ INPUT
    for i in trainingSet:
        i[0]/=100
        i[1]/=100
        i[2]/=100
        i[3]/=100
        
    #mapping
    temp=set()
    for i in array_right:
        temp.add(i[0])
    temp=list(temp)
    mapping={ value: index for index, value in enumerate(temp)}
    mapping1={ index: value for index, value in enumerate(temp)}

    for i in array_right:
        i[0]=mapping[i[0]]


    trainingSetNumpy=np.array(trainingSet)

    m,n=trainingSetNumpy.shape

    np.random.shuffle(trainingSetNumpy)

    X_dev=trainingSetNumpy.T
    Y_dev=np.squeeze(np.array(array_right).T)
   

    def init_params():
        # MA TRẬN TRỌNG SỐ
        global temp
        W1 = np.random.rand(30, 4) 
        b1 = np.random.rand(30, 1) 
        W2 = np.random.rand(len(temp), 30) 
        b2 = np.random.rand(len(temp), 1)
        return W1, b1, W2, b2

    def ReLU(Z):
        return np.maximum(Z, 0)

    def softmax(Z):
        A = np.exp(Z) / sum(np.exp(Z))
        return A
        
    def forward_prop(W1, b1, W2, b2, X):
        Z1 = W1.dot(X) + b1
        A1 = ReLU(Z1)
        Z2 = W2.dot(A1) + b2
        A2 = softmax(Z2)
        return Z1, A1, Z2, A2

    def ReLU_deriv(Z):
        
        return np.where(Z > 0, 1, 0)
        
    # BIẾN NHÃN THÀNH ONE HOT LABEL (KD:1 0 0, PD: 0 1 0, NV 0 0 1)
    def one_hot(Y):
        one_hot_Y = np.zeros((Y.size, (int)(Y.max() + 1)))
        one_hot_Y[np.arange(Y.size), Y.astype(int)] = 1
        one_hot_Y = one_hot_Y.T
        return one_hot_Y

    def backward_prop(Z1, A1, Z2, A2, W1, W2, X, Y):
        one_hot_Y = one_hot(Y)
        dZ2 = A2 - one_hot_Y
        dW2 = 1 / m * dZ2.dot(A1.T)
        db2 = 1 / m * np.sum(dZ2)
        dZ1 = W2.T.dot(dZ2) * ReLU_deriv(Z1)
        dW1 = 1 / m * dZ1.dot(X.T)
        db1 = 1 / m * np.sum(dZ1)
        return dW1, db1, dW2, db2

    def update_params(W1, b1, W2, b2, dW1, db1, dW2, db2, alpha):
        W1 = W1 - alpha * dW1
        b1 = b1 - alpha * db1    
        W2 = W2 - alpha * dW2  
        b2 = b2 - alpha * db2    
        return W1, b1, W2, b2
    
    def get_predictions(A2):
        return np.argmax(A2, 0)

    def get_accuracy(predictions, Y):
        print(predictions, Y)
        return np.sum(predictions == Y) / Y.size
    # HÀM TRAINING
    def gradient_descent(X, Y, alpha, iterations):
        W1, b1, W2, b2 = init_params()
        for i in range(iterations):
            Z1, A1, Z2, A2 = forward_prop(W1, b1, W2, b2, X)
            dW1, db1, dW2, db2 = backward_prop(Z1, A1, Z2, A2, W1, W2, X, Y)
            W1, b1, W2, b2 = update_params(W1, b1, W2, b2, dW1, db1, dW2, db2, alpha)
            if i % 200 == 0:
                print("Iteration: ", i)
                predictions = get_predictions(A2)
                print(get_accuracy(predictions, Y))
        return W1, b1, W2, b2

    # TRỌNG SỐ VÀ BIAS CỦA MẠNG PL
    W1PL, b1PL, W2PL, b2PL = gradient_descent(X_dev, Y_dev, 0.0003, 10000)

    #DỰ ĐOÁN 
    def make_predictions(X, W1, b1, W2, b2):
        _, _, _, A2 = forward_prop(W1, b1, W2, b2, X)
        predictions = get_predictions(A2)
        return predictions
    def getDisease(X, W1, b1, W2, b2):
        global mapping1
        pre=make_predictions(X, W1, b1, W2, b2)
        return mapping1[(int)(pre[0])]
    # KIỂM TRA XEM NHÃN THỰC VÀ DỰ ĐOÁN CÓ GIỐNG NHAU
    def test_prediction(index, W1, b1, W2, b2):
        prediction = make_predictions(X_dev[:, index, None], W1, b1, W2, b2)
        label = Y_dev[index]
        print("Prediction: ", prediction)
        print("Label: ", label)

    db.create_all()

############# API
@app.route('/add', methods=['POST'])
def add_data():
    # data = request.json
    data = request.args

    temperature = data.get('temperature')
    humidity = data.get('humidity')
    spo = data.get('spo')
    heartbeat = data.get('heartbeat')
    disease = data.get('disease')

    new_data = Datas(temperature=temperature, humidity=humidity, spo=spo, heartbeat=heartbeat, disease=disease)

    db.session.add(new_data)
    db.session.commit()

    return jsonify({'message': 'Data added successfully'})

@app.route('/checkstatus', methods=['GET'])
def current_status():
    data = request.args
    temperature = (float)(data.get('temperature'))
    humidity = (float)(data.get('humidity'))
    spo = (float)(data.get('spo'))
    heartbeat = (float)(data.get('heartbeat'))
    input=[temperature,humidity,spo,heartbeat]
    input=np.array(input)
    input=input.reshape(-1, 1)
    global W1PL, b1PL,W2PL,b2PL
    print(W1PL)
    status= getDisease(input,W1PL,b1PL,W2PL,b2PL)


    return jsonify({'message': status})

@app.route('/get-all', methods=['GET'])
def get_all_data():
    datas = Datas.query.all()

    data_list = []
    for data in datas:
        data_dict = {
            'id': data.id,
            'temperature': data.temperature,
            'humidity': data.humidity,
            'spo': data.spo,
            'heartbeat': data.heartbeat,
            'disease': data.disease
        }
        data_list.append(data_dict)

    return jsonify(data_list)

if __name__ == '__main__':
    app.run()