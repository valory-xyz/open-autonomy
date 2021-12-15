from flask import Flask
from flask import Response
app = Flask(__name__)

@app.route("/gentle_reset")
def gentle_reset():
    return Response("Success",
                    status=200,
                    mimetype='application/json')

@app.route("/hard_reset")
def hard_reset():
    return Response("Success",
                    status=200,
                    mimetype='application/json')


@app.errorhandler(404)
def handle_notfound(e):
    return Response("Not Found",
                    status=404,
                    mimetype='application/json')

    return (404, 'we could not find the page')

@app.errorhandler(500)
def handle_server_error(e):
    return Response("Error Closing Node",
                    status=500,
                    mimetype='application/json')



if __name__ == "__main__":
    app.run()
