import os

from flask import Flask, render_template, request

from web.loader import load, logger, node_db_handler, account_db_handler
from web.server.blueprints.service import api


__config_path = os.getcwd().split('\\')
__config_path = __config_path[:__config_path.index('web') + 1]
__config_location = '\\'.join(__config_path)
__ok, __info = load(__config_location)


app = Flask(__name__)
app.register_blueprint(api, url_prefix='/api')
app.secret_key = os.urandom(12)


@app.route('/', methods=['GET', 'POST'])
def main():
    if request.method == 'GET':
        data = node_db_handler.access().get_nodes()

        return render_template('index.html', **data)
    else:
        node_id = request.form['node_id']

        return node_info(node_id)


# @app.route('/login', methods=['POST'])
# def login():
#     if request.method == 'GET':
#         pass
#     elif request.method == 'POST':
#         pass
#
#
# @app.route('/logout', methods=['POST'])
# def logout():
#     if request.method == 'POST':
#         pass


@app.route('/nodes/<string:id>', methods=['GET'])
def node_info(id):
    logger.access().warning("'{}' is trying to access information about node '{}'".format(request.remote_addr, id))
    ok, data = node_db_handler.access().get_node_info(id)
    return render_template('node.html', **data)


if __name__ == '__main__':
    # port 8181 default
    app.debug = False
    logger.access().info("Server running at localhost:5000")
    print("Run at {}".format('localhost:5000'))
    app.run(host='0.0.0.0')
    # app.run('localhost')
