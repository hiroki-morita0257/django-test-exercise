from django.shortcuts import render, redirect
from django.http import Http404
from django.utils import timezone
from django.utils.timezone import make_aware
from django.utils.dateparse import parse_datetime
from todo.models import Task


def get_min_due_at():
    return timezone.localtime(timezone.now()).strftime('%Y-%m-%dT%H:%M')

# Create your views here.


def index(request):
    if request.method == 'POST':
        due_at = request.POST.get('due_at')

        if due_at:
            parsed_due_at = make_aware(parse_datetime(due_at))

            if parsed_due_at < timezone.now():
                context = {
                    'tasks': Task.objects.order_by('-posted_at'),
                    'min_due_at': get_min_due_at(),
                }
                return render(request, 'todo/index.html', context)
        else:
            parsed_due_at = None

        memo = request.POST.get('memo', '')
        task = Task(
            title=request.POST['title'],
            due_at=parsed_due_at,
            memo=memo,
        )
        task.save()

    if request.GET.get('order') == 'due':
        tasks = Task.objects.order_by('due_at')
    else:
        tasks = Task.objects.order_by('-posted_at')

    context = {
        'tasks': tasks,
        'min_due_at': get_min_due_at(),
    }
    return render(request, 'todo/index.html', context)


def detail(request, task_id):
    try:
        task = Task.objects.get(pk=task_id)
    except Task.DoesNotExist:
        raise Http404("Task does not exist")

    context = {
        'task': task,
    }
    return render(request, 'todo/detail.html', context)


def update(request, task_id):
    try:
        task = Task.objects.get(pk=task_id)
    except Task.DoesNotExist:
        raise Http404("Task dose not exist")

    if request.method == 'POST':
        due_at = request.POST.get('due_at')

        if due_at:
            parsed_due_at = make_aware(parse_datetime(due_at))

            if parsed_due_at < timezone.now():
                context = {
                    'task': task,
                    'min_due_at': get_min_due_at(),
                }
                return render(request, 'todo/edit.html', context)
        else:
            parsed_due_at = None

        task.title = request.POST['title']
        task.due_at = parsed_due_at
        task.memo = request.POST.get('memo', '')
        task.save()

        return redirect(detail, task_id)

    context = {
        'task' : task,
        'min_due_at': get_min_due_at(),
    }
    return render(request, "todo/edit.html", context)

  
def delete(request, task_id):
    try:
        task = Task.objects.get(pk=task_id)
    except Task.DoesNotExist:
        raise Http404("Task does not exist")
    task.delete()
    return redirect(index)
