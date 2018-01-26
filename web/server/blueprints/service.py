from flask import Blueprint, render_template, request, json, Response

from web.loader import logger, node_db_handler, account_db_handler


api = Blueprint('api', __name__)


@api.route('/')
def show_calls():
    return render_template('api.html')


@api.route('/get_node_data')
def get_node_data():
    logger.access().warning("'{}' is trying to access node data".format(request.remote_addr))
    api_key = request.args.get('api_key', '')

    if api_key == '':
        # unauthorized!
        return Response("API key required", status=400)

    # else there is some API key...
    ok, message = account_db_handler.access().is_valid_api_key(api_key)

    if ok:
        logger.access().info(message)
        data = node_db_handler.access().get_data(True)
        js = json.dumps(data)

        resp = Response(js, status=200, mimetype='application/json', content_type='application/json')
    else:
        resp = Response(message, status=400)

    return resp
