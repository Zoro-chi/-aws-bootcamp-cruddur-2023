from datetime import datetime, timedelta, timezone
class ShowActivities:
  def run(activity_uuid):
    now = datetime.now(timezone.utc).astimezone()
    results = [{
      'uuid': '68f126b0-1ceb-4a33-88be-d90fa7109eee',
      'handle':  'Andrew Brown',
      'message': 'Cloud is fun!',
      'created_at': (now - timedelta(days=2)).isoformat(),
      'expires_at': (now + timedelta(days=5)).isoformat(),
      'replies': {
        'uuid': '26e12864-1c26-5c3a-9658-97a10f8fea67',
        'handle':  'Worf',
        'message': 'This post has no honor!',
        'created_at': (now - timedelta(days=2)).isoformat()
      }
    }, {
      'uuid': '66b8132b1-d68d-4d05-93af-a646e0d1edf7',
      'handle':  'Zoro',
      'message': 'Murkin!',
      'created_at': (now - timedelta(days=2)).isoformat(),
      'expires_at': (now + timedelta(days=5)).isoformat(),
      'replies': {
        'uuid': '26e12864-1c26-5c3a-9658-97a10f8fea67',
        'handle':  'Jack',
        'message': 'The Drought is coming!',
        'created_at': (now - timedelta(days=2)).isoformat()
      }
    }]
    return results