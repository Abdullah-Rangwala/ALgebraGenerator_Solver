from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.core.serializers import serialize
import random
from sympy import symbols, Eq, solve
from .models import History
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required

from django.views.decorators.csrf import csrf_exempt
import logging

from .forms import CustomUserCreationForm

logger = logging.getLogger(__name__)


@login_required
def home(request):
    """Render the home page."""
    return render(request, 'expression/index.html')


def generate_equation(request):
    """Generate a random equation based on the type (linear, quadratic, polynomial)."""
    equation_type = request.GET.get('type', 'linear')

    if equation_type == 'linear':
        # LOCKED: Linear equation generation
        # Generate a random linear equation: ax + b = c
        a = random.randint(1, 10)
        b = random.randint(1, 10)
        c = random.randint(1, 10)
        equation = f"{a}x + {b} = {c}"
        return JsonResponse({
            "equation": equation,
            "a": a,
            "b": b,
            "c": c
        })

    elif equation_type == 'quadratic':
        # LOCKED: Quadratic equation generation
        # Generate a random quadratic equation: ax^2 + bx + c = 0
        while True:
            a = random.randint(1, 10)
            b = random.randint(1, 10)
            c = random.randint(1, 10)
            discriminant = b**2 - 4*a*c
            if discriminant >= 0:  # Ensure real roots
                break
        equation = f"{a}x^2 + {b}x + {c} = 0"
        return JsonResponse({
            "equation": equation,
            "a": a,
            "b": b,
            "c": c
        })

    elif equation_type == 'polynomial':
        # MODIFY: Polynomial equation generation
        # Randomly choose the degree of the polynomial (3 to 5)
        degree = random.randint(3, 5)

        while True:
            # Generate random coefficients for the polynomial
            coefficients = [random.randint(1, 10) for _ in range(degree + 1)]

            # Construct the polynomial equation
            x = symbols('x')
            polynomial_eq = sum(coeff * x**(degree - i) for i, coeff in enumerate(coefficients))

            # Solve the polynomial equation
            roots = solve(polynomial_eq, x)
            # Convert SymPy Float to Python float
            real_roots = [float(root.evalf()) for root in roots if root.is_real]

            # If real roots exist, break the loop
            if real_roots:
                break

        # Construct the polynomial equation string in descending order of degree
        equation_str = " + ".join(
            f"{coeff}x^{degree - i}" if degree - i > 1 else (f"{coeff}x" if degree - i == 1 else f"{coeff}")
            for i, coeff in enumerate(coefficients)
        ) + " = 0"

        return JsonResponse({
            "equation": equation_str,
            "coefficients": coefficients,
            "real_roots": real_roots
        })

    else:
        return JsonResponse({"error": "Invalid equation type"}, status=400)


@login_required
def solve_equation(request):
    try:
        if not request.user.is_authenticated:
            return JsonResponse({'error': 'User not authenticated'}, status=401)

        # Get parameters from the request
        equation_type = request.GET.get('type', 'linear')
        user_answer = float(request.GET.get('answer', 0))

        if equation_type == 'linear':
            # LOCKED: Linear equation solving
            a = int(request.GET.get('a', 1))
            b = int(request.GET.get('b', 0))
            c = int(request.GET.get('c', 0))
            correct_answer = (c - b) / a
            equation = f"{a}x + {b} = {c}"

        elif equation_type == 'quadratic':
            # Fix: Correctly solve quadratic equations using the quadratic formula
            a = int(request.GET.get('a', 1))
            b = int(request.GET.get('b', 0))
            c = int(request.GET.get('c', 0))

            discriminant = b**2 - 4*a*c
            if discriminant < 0:
                correct_answer = None  # No real roots
            else:
                root1 = (-b + discriminant**0.5) / (2 * a)
                root2 = (-b - discriminant**0.5) / (2 * a)
                correct_answer = round(min(root1, root2), 3)  # Return the smaller root for simplicity

            equation = f"{a}x^2 + {b}x + {c} = 0"

        elif equation_type == 'polynomial':
            # Handle polynomial equation solving
            degree = int(request.GET.get('degree', 3))  # Default to degree 3
            coefficients = [
                int(request.GET.get(f'coeff{i}', 0)) for i in range(degree + 1)
            ]

            # Construct the polynomial equation
            x = symbols('x')
            polynomial_eq = sum(coeff * x**(degree - i) for i, coeff in enumerate(coefficients))
            roots = solve(polynomial_eq, x)

            # Convert SymPy Float to Python float
            real_roots = [float(root.evalf()) for root in roots if root.is_real]
            correct_answer = real_roots[0] if real_roots else None

            # Construct the polynomial equation string
            equation = " + ".join(
                f"{coeff}x^{degree - i}" if degree - i > 1 else (f"{coeff}x" if degree - i == 1 else f"{coeff}")
                for i, coeff in enumerate(coefficients)
            ) + " = 0"

        else:
            return JsonResponse({"error": "Invalid equation type"}, status=400)

        # Round the correct answer to 3 decimal places
        if correct_answer is not None:
            correct_answer = round(correct_answer, 3)

        # Check if the user's answer is correct
        is_correct = bool(correct_answer is not None and abs(user_answer - correct_answer) < 0.01)

        # Save the solved equation to the History model
        History.objects.create(
            user=request.user,
            equation=equation,
            user_answer=user_answer,
            correct_answer=correct_answer,
            is_correct=is_correct
        )

        # Return the response
        return JsonResponse({
            "is_correct": is_correct,
            "correct_answer": correct_answer,
            "equation": equation
        })
    except Exception as e:
        logger.error(f"Error in solve_equation: {str(e)}")
        return JsonResponse({"error": str(e)}, status=500)


@login_required
def get_history(request):
    history = History.objects.filter(user=request.user).order_by('-timestamp')
    if not history.exists():
        return JsonResponse({'history': []})

    history_data = [
        {
            "equation": entry.equation,
            "user_answer": entry.user_answer,
            "correct_answer": entry.correct_answer,
            "is_correct": entry.is_correct,
            "timestamp": entry.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
        }
        for entry in history
    ]
    return JsonResponse({'history': history_data})


@csrf_exempt
@login_required
def clear_history(request):
    if request.method == 'POST':
        History.objects.filter(user=request.user).delete()
        return JsonResponse({'success': True, 'message': 'History cleared successfully.'})
    return JsonResponse({'success': False, 'message': 'Invalid request method.'}, status=400)


def register(request):
    if request.user.is_authenticated:
        return redirect('home')
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            print("Form is valid")  # Debugging
            form.save()
            return redirect('login')
        else:
            print("Form errors:", form.errors)  # Debugging
    else:
        form = CustomUserCreationForm()
    return render(request, 'expression/register.html', {'form': form})
