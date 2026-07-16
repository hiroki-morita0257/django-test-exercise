from django.test import TestCase, Client
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from datetime import datetime
from todo.models import Task

# Create your tests here.


class SampleTestCase(TestCase):
    def test_sample(self):
        self.assertEqual(1 + 2, 3)


class TaskModelTestCase(TestCase):
    def test_create_task1(self):
        due = timezone.make_aware(datetime(2024, 6, 30, 23, 59, 59))
        task = Task(title='task1', due_at=due)
        task.save()

        task = Task.objects.get(pk=task.pk)
        self.assertEqual(task.title, 'task1')
        self.assertFalse(task.completed)
        self.assertEqual(task.due_at, due)

    def test_create_task2(self):
        task = Task(title='task2')
        task.save()

        task = Task.objects.get(pk=task.pk)
        self.assertEqual(task.title, 'task2')
        self.assertFalse(task.completed)
        self.assertEqual(task.due_at, None)

    def test_is_overdue_future(self):
        due = timezone.make_aware(datetime(2024, 6, 30, 23, 59, 59))
        current = timezone.make_aware(datetime(2024, 6, 30, 0, 0, 0))
        task = Task(title='task1', due_at=due)
        task.save()

        self.assertFalse(task.is_overdue(current))

    def test_is_overdue_past(self):
        due = timezone.make_aware(datetime(2024, 6, 30, 23, 59, 59))
        current = timezone.make_aware(datetime(2024, 7, 1, 0, 0, 0))
        task = Task(title='task1', due_at=due)
        task.save()

        self.assertTrue(task.is_overdue(current))

    def test_is_overdue_none(self):
        current = timezone.make_aware(datetime(2024, 7, 1, 0, 0, 0))
        task = Task(title='task1')
        task.save()

        self.assertFalse(task.is_overdue(current))

    def test_memo_default_blank(self):
        task = Task(title='task-without-memo')
        task.save()

        task = Task.objects.get(pk=task.pk)
        self.assertEqual(task.memo, '')


class TodoViewTestCase(TestCase):
    def test_index_get(self):
        client = Client()
        response = client.get('/')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.templates[0].name, 'todo/index.html')
        self.assertEqual(len(response.context['tasks']), 0)

    def test_index_get_contains_min_due_at(self):
        client = Client()
        response = client.get('/')

        self.assertEqual(response.status_code, 200)
        self.assertIn('min_due_at', response.context)
        self.assertRegex(response.context['min_due_at'], r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}$')

    def test_index_post(self):
        client = Client()
        future_time = timezone.localtime(
            timezone.now() + timezone.timedelta(hours=1)
        ).strftime('%Y-%m-%dT%H:%M')
        data = {'title': 'Test Task', 'due_at': future_time}
        response = client.post('/', data)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.templates[0].name, 'todo/index.html')
        self.assertEqual(len(response.context['tasks']), 1)

    def test_index_post_rejects_past_due_at(self):
        client = Client()
        past_time = (timezone.now() - timezone.timedelta(hours=1)).strftime('%Y-%m-%dT%H:%M')
        response = client.post('/', {'title': 'Past Task', 'due_at': past_time})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(Task.objects.filter(title='Past Task').count(), 0)

    def test_index_get_order_post(self):
        task1 = Task(title='task1', due_at=timezone.make_aware(datetime(2024, 7, 1)))
        task1.save()
        task2 = Task(title='task2', due_at=timezone.make_aware(datetime(2024, 8, 1)))
        task2.save()
        client = Client()
        response = client.get('/?order=post')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.templates[0].name, 'todo/index.html')
        self.assertEqual(response.context['tasks'][0], task2)
        self.assertEqual(response.context['tasks'][1], task1)

    def test_index_get_order_due(self):
        task1 = Task(title='task1', due_at=timezone.make_aware(datetime(2024, 7, 1)))
        task1.save()
        task2 = Task(title='task2', due_at=timezone.make_aware(datetime(2024, 8, 1)))
        task2.save()
        client = Client()
        response = client.get('/?order=due')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.templates[0].name, 'todo/index.html')
        self.assertEqual(response.context['tasks'][0], task1)
        self.assertEqual(response.context['tasks'][1], task2)

    def test_detail_get_success(self):
        task = Task(title='task1', due_at=timezone.make_aware(datetime(2024, 7, 1)))
        task.save()
        client = Client()
        response = client.get('/{}/'.format(task.pk))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.templates[0].name, 'todo/detail.html')
        self.assertEqual(response.context['task'], task)

    def test_detail_get_fail(self):
        client = Client()
        response = client.get('/1/')

        self.assertEqual(response.status_code, 404)

    def test_delete_get_success(self):
        task = Task(title='task1', due_at=timezone.make_aware(datetime(2024, 7, 1)))
        task.save()
        client = Client()

        response = client.get('/{}/delete'.format(task.pk))

        self.assertEqual(response.status_code, 302)
        self.assertFalse(Task.objects.filter(pk=task.pk).exists())

    def test_delete_get_fail(self):
        client = Client()
        response = client.get('/1/delete')

        self.assertEqual(response.status_code, 404)

    def test_update_get_success(self):
        task = Task(title='task1', due_at=timezone.make_aware(datetime(2024, 7, 1)))
        task.save()
        client = Client()

        response = client.get('/{}/update'.format(task.pk))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.templates[0].name, 'todo/edit.html')
        self.assertEqual(response.context['task'], task)

    def test_update_get_contains_min_due_at(self):
        task = Task(title='task1', due_at=timezone.make_aware(datetime(2024, 7, 1)))
        task.save()
        client = Client()

        response = client.get('/{}/update'.format(task.pk))

        self.assertEqual(response.status_code, 200)
        self.assertIn('min_due_at', response.context)
        self.assertRegex(response.context['min_due_at'], r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}$')

    def test_update_get_fail(self):
        client = Client()
        response = client.get('/1/update')

        self.assertEqual(response.status_code, 404)

    def test_update_post_success(self):
        task = Task(title='task1', due_at=timezone.make_aware(datetime(2024, 7, 1)))
        task.save()
        client = Client()
        future_time = timezone.localtime(
            timezone.now() + timezone.timedelta(hours=2)
        ).strftime('%Y-%m-%dT%H:%M')
        data = {
            'title': 'updated task',
            'due_at': future_time,
        }

        response = client.post('/{}/update'.format(task.pk), data)

        self.assertEqual(response.status_code, 302)

        task = Task.objects.get(pk=task.pk)
        self.assertEqual(task.title, 'updated task')
        self.assertEqual(task.due_at, timezone.make_aware(parse_datetime(future_time)))

    def test_update_post_rejects_past_due_at(self):
        task = Task(title='task1', due_at=timezone.make_aware(datetime(2024, 7, 1)))
        task.save()
        client = Client()
        past_time = (timezone.now() - timezone.timedelta(hours=1)).strftime('%Y-%m-%dT%H:%M')

        response = client.post('/{}/update'.format(task.pk), {'title': 'updated task', 'due_at': past_time})

        self.assertEqual(response.status_code, 200)
        task.refresh_from_db()
        self.assertEqual(task.title, 'task1')
        self.assertEqual(task.due_at, timezone.make_aware(datetime(2024, 7, 1)))

    def test_update_post_fail(self):
        client = Client()
        data = {
            'title': 'updated task',
            'due_at': '2024-08-01 12:00:00',
        }

        response = client.post('/1/update', data)

        self.assertEqual(response.status_code, 404)

    def test_index_post_with_memo(self):
        client = Client()
        data = {'title': 'Task with memo', 'due_at': '2024-06-30 23:59:59', 'memo': 'Remember this'}
        response = client.post('/', data)

        # index view returns the page with tasks in context
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['tasks']), 1)

        task = Task.objects.first()
        self.assertIsNotNone(task)
        self.assertEqual(task.memo, 'Remember this')

    def test_update_post_updates_memo(self):
        task = Task(title='task1', due_at=timezone.make_aware(datetime(2024, 7, 1)))
        task.save()
        client = Client()
        data = {
            'title': 'updated with memo',
            'due_at': '2024-08-01 12:00:00',
            'memo': 'Updated memo content',
        }

        response = client.post('/{}/update'.format(task.pk), data)

        self.assertEqual(response.status_code, 302)

        task = Task.objects.get(pk=task.pk)
        self.assertEqual(task.title, 'updated with memo')
        self.assertEqual(task.memo, 'Updated memo content')
