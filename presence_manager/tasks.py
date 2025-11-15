from apscheduler.schedulers.background import BackgroundScheduler
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync


def start_presence_scheduler():
    scheduler = BackgroundScheduler()
    iteration = {"count": 0}

    def send_message():
        iteration["count"] += 1
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            "presence_group",
            {
                "type": "send_presence_message",
                "message": {"message": f"debut premier cours {iteration['count']}"},
            },
        )
        print(f"[Scheduler] Message envoyé : {iteration['count']}")

    scheduler.add_job(send_message, "interval", seconds=1)
    scheduler.start()
