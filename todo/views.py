from django.shortcuts import render, redirect
from django.http import Http404
from django.utils.timezone import make_aware
from django.utils.dateparse import parse_datetime
from todo.models import Task

# Create your views here.


def index(request):
    if request.method == 'POST':
        due_at = request.POST.get('due_at')
        if due_at:
            due_at = make_aware(parse_datetime(due_at))
        else:
            due_at = None
        memo = request.POST.get('memo', '')
        task = Task(title=request.POST['title'], due_at=due_at, memo=memo)
        task.save()

    if request.GET.get('order') == 'due':
        tasks = Task.objects.order_by('due_at')
    else:
        tasks = Task.objects.order_by('-posted_at')

    context = {
        'tasks': tasks,
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
        task.title = request.POST['title']
        due_at = request.POST.get('due_at')
        if due_at:
            task.due_at = make_aware(parse_datetime(due_at))
        else:
            task.due_at = None
        task.memo = request.POST.get('memo', '')
        task.save()
        return redirect(detail, task_id)

    context = {
        'task' : task
    }
    return render(request, "todo/edit.html", context)

  
def delete(request, task_id):
    try:
        task = Task.objects.get(pk=task_id)
    except Task.DoesNotExist:
        raise Http404("Task does not exist")
    task.delete()
    return redirect(index)
