from flask import Flask ,Response , render_template, request, jsonify
from prometheus_flask_exporter import PrometheusMetrics
from jaeger_client import Config
import logging
from flask_opentracing import FlaskTracing


import pymongo
from flask_pymongo import PyMongo

app = Flask(__name__)
metrics = PrometheusMetrics(app)
JAEGER_DOMAIN_NAME = 'traces-collection-agent.observability.svc.cluster.local'

metrics.info('app_info', 'Application info', version='1.0.3')

def init_tracer(service='backend'):
    logging.getLogger('').handlers = []
    logging.basicConfig(format='%(message)s', level=logging.DEBUG)    
    config = Config(
        config={
            'logging': True,
        },
        service_name=service,
    )
    return config.initialize_tracer()

jaeger_tracer = init_tracer('backend')
tracing = FlaskTracing(jaeger_tracer, True, app)

app.config["MONGO_DBNAME"] = "example-mongodb"
app.config[
    "MONGO_URI"
] = "mongodb://example-mongodb-svc.default.svc.cluster.local:27017/example-mongodb"

mongo = PyMongo(app)


@app.route("/")
def homepage():
    if request.headers['error'] == 'client':
        return Response(status=404)
    if request.headers['error'] == 'server':
        return Response(status=504)
    return "Hello World"


@app.route("/api")
def my_api():
    answer = "something"
    return jsonify(repsonse=answer)


@app.route("/star", methods=["POST"])
def add_star():
    star = mongo.db.stars
    name = request.json["name"]
    distance = request.json["distance"]
    star_id = star.insert({"name": name, "distance": distance})
    new_star = star.find_one({"_id": star_id})
    output = {"name": new_star["name"], "distance": new_star["distance"]}
    return jsonify({"result": output})


if __name__ == "__main__":
    app.run()
