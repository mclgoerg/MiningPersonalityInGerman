from flask import Flask
from flask import request
from flask import jsonify

from .requestHandler import RequestHandler
from .invalidUsage import InvalidUsage
from ..application.modelApplication import ModelApplication
from ..models.profile import Profile
from ..training.dataPreparation import DataPreparation


app = Flask(__name__)
# set config for app
app.config['CAPTCHAKEY'] = (
    RequestHandler.loadKey(name="google_recaptcha")
)
app.config['twitter_consumer_key'] = (
    RequestHandler.loadKey(name="twitter_consumer_key")
)
app.config['twitter_consumer_secret'] = (
    RequestHandler.loadKey(name="twitter_consumer_secret")
)
app.config['glove_file_path'] = (
    RequestHandler.loadKey(name="glove_file_path")
)
app.config['glove_database_mode'] = (
    RequestHandler.loadKey(name="glove_database_mode")
)


@app.route("/test")
def testAPI():
    """
    Simple test code, to check if API is set up correctly.
    Will always be available, when server is running.
    """
    if app.config['CAPTCHAKEY'] == "":
        captcha = Falseg
    else:
        captcha = True
    if (
        app.config['twitter_consumer_key'] == "" or
        app.config['twitter_consumer_secret'] == ""
    ):
        twitterString = "Twitter keys are missing in .env."
    else:
        twitterString = "Twitter keys are set."

    returnString = (
        "<h1 style='color:Black'>MiPing Backend is up and running. " +
        "reCaptcha is set to: " +
        str(captcha) +
        " . " +
        twitterString +
        "</h1>"
    )
    return returnString


@app.route('/personality', methods=['POST'])
def parse_request():
    """
    Accept user name and return personality profile.
    """

    if request is None:
        raise InvalidUsage('No data provided', status_code=400)

    # read incoming data as json
    data = request.get_json()

    if data is None:
        raise InvalidUsage('No data provided', status_code=400)

    # initialize requestHandler
    requestHandler = RequestHandler(
        config=app.config
    )

    # determine if captcha check is necessary
    if app.config['CAPTCHAKEY'] != "":
        # check is necessary
        result = requestHandler.check_recaptcha(data)

        if result is False:
            raise InvalidUsage('Invalid reCaptcha', status_code=400)

    # captcha is valid (if check was performed)
    # now validate user name input
    userName = requestHandler.validate_username_input(data)

    # get personality
    returnDict = requestHandler.get_personality(username=userName)

    return returnDict

@app.route('/hello')
def hello():
    return 'Hello, World'

@app.route('/slack')
def slack_parse_request():
    """
    Accept user name and return personality profile.
    """
    # initialize requestHandler
    requestHandler = RequestHandler(
        config=app.config
    )
    dataPre = DataPreparation()
    textString = dataPre.clean_text(
        textString='Der Bundestag hat die Pflicht der Abgeordneten zur Anwesenheit im Parlament gelockert.'
    )
    profile = Profile(
            userID='1',
            text=textString
        )
    # get personality
    returnDict = requestHandler.get_slack_personality(profile=profile)
    
    return returnDict

@app.route('/slackpost', methods=['Post'])
def slackpost_parse_request():
    """
    Accept user name and return personality profile.
    """
    if request is None:
        raise InvalidUsage('No data provided', status_code=400)

    # read incoming data as json
    data = request.get_json()

    if data is None:
        raise InvalidUsage('No data provided', status_code=400)
    
    if 'slackMessage' in data:
        handleData = data['slackMessage']
    else:
            # key does not exist, invalid request
            raise InvalidUsage('No slack message provided', status_code=400)
    # initialize requestHandler
    requestHandler = RequestHandler(
        config=app.config
    )
    dataPre = DataPreparation()
    textString = dataPre.clean_text(
        textString=handleData
    )
    print(textString)
    profile = Profile(
            userID='1',
            text=textString
        )
    # get personality
    returnDict = requestHandler.get_slack_personality(profile=profile)
    
    return returnDict


@app.errorhandler(InvalidUsage)
def handle_invalid_usage(error):
    response = jsonify(error.to_dict())
    response.status_code = error.status_code
    return response


if __name__ == "__main__":
    app.run(host='127.0.0.1')
