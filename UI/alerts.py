#
# Mario Torre - 04/20/2023
#
import time

def set_alert_message (alert, message, type, show_time):
    alert.object = "<div>" + message + "</div>"
    alert.visible = True
    alert.alert_type = type
    time.sleep(show_time)
    alert.visible = False


def show_alert_general(alert, e, pitems, panel_config):
        set_alert_message (pitems.main_alert, panel_config["alerts"]["messages"][str(alert)]["text"].format(str(e)), \
            type = panel_config["alerts"]["types"][panel_config["alerts"]["messages"][str(alert)]["severity"]], \
            show_time = panel_config["alerts"]["messages"][str(alert)]["time"])
        return