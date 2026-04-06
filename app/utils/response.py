from flask import jsonify

"""
This is the code of response patterns that will be accepted
by the API, all requisitions will follow the rules bellow

successful_response: data, status_code(200) => {"sucess": "true", "data": data, "status_code": status_code}
error_response: err, status_code(401) => {"sucess": "false", "error_msg":err.__repr__(), "status_code":status_code}
"""

def successful_response(data, status_code=200):
    return jsonify({
        "success":True,
        "data":data,
        "status_code":status_code
    })

def error_response(err, status_code=401):
    return jsonify({
        "success": False,
        "error_msg": err.__repr__(),
        "status_code": status_code
    })
