from logging import log
from flask import Flask
from flask import Response
import logging
from tendermint import TendermintNode, TendermintParams

app = Flask(__name__)

@app.route("/gentle_reset")
def gentle_reset():
    tendermint_node.stop()
    tendermint_node.start()
    return Response("Success",
                    status=200,
                    mimetype='application/json')

@app.route("/hard_reset")
def hard_reset():
    tendermint_node.stop()
    tendermint_node.prune_blocks()
    tendermint_node.start()
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


import os

if __name__ == "__main__":
    id = f"{os.environ.get('ID', 1)}"
    home = f"/tendermint/node{id}"

    os.environ['TMHOME'] = home
    
    tendermint_params = TendermintParams(
        proxy_app=f"tcp://abci{id}:26658",
        consensus_create_empty_blocks=True,
        home=home
    )
    tendermint_node = TendermintNode(tendermint_params)
    tendermint_node.start()
    app.run()
