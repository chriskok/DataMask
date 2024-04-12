from django.db.models import F
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.views import generic

import json
import requests

from .models import *
from .forms import *
from .ner import *
from .masking import *

class IndexView(generic.ListView):
    template_name = "llm_anon_app/index.html"
    context_object_name = "latest_question_list"

    def get_queryset(self):
        """Return the last five published questions."""
        return Question.objects.order_by("-pub_date")[:5]

class DetailView(generic.DetailView):
    model = Question
    template_name = "llm_anon_app/detail.html"

class ResultsView(generic.DetailView):
    model = Question
    template_name = "llm_anon_app/results.html"

def vote(request, question_id):
    question = get_object_or_404(Question, pk=question_id)
    try:
        selected_choice = question.choice_set.get(pk=request.POST["choice"])
    except (KeyError, Choice.DoesNotExist):
        # Redisplay the question voting form.
        return render(
            request,
            "llm_anon_app/detail.html",
            {
                "question": question,
                "error_message": "You didn't select a choice.",
            },
        )
    else:
        selected_choice.votes = F("votes") + 1
        selected_choice.save()
        # Always return an HttpResponseRedirect after successfully dealing
        # with POST data. This prevents data from being posted twice if a
        # user hits the Back button.
        return HttpResponseRedirect(reverse("llm_anon_app:results", args=(question.id,)))
    
def ner(request, session_id=None):

    # if no UseCase exists, create some defaults
    if not UseCase.objects.exists():
        UseCase.objects.create(use_case="Therapy")
        UseCase.objects.create(use_case="Nursing")
        UseCase.objects.create(use_case="Law")
        
    therapy = UseCase.objects.get(use_case="Therapy")
    nursing = UseCase.objects.get(use_case="Nursing")
    law = UseCase.objects.get(use_case="Law")
        
    if not EvalQuestion.objects.exists():
        EvalQuestion.objects.create(use_case=therapy, 
                                    pub_date=timezone.now(),
                                    question_text="To what extent do the details and descriptions in the deanonymized LLM-generated notes match the level of specificity and nuance typically found in handwritten clinical notes?")
        EvalQuestion.objects.create(use_case=therapy,
                                    pub_date=timezone.now(),
                                    question_text="Do the deanonymized LLM-generated treatment plan and next steps align with best practices for person-centered, goal-oriented therapy planning?")
        EvalQuestion.objects.create(use_case=therapy,
                                    pub_date=timezone.now(),
                                    question_text="Would a client feel their personal experiences and unique perspectives are adequately represented in the deanonymized LLM-generated notes versus handwritten ones?")
        EvalQuestion.objects.create(use_case=therapy,
                                    pub_date=timezone.now(),
                                    question_text="Are there any notable gaps, errors, or concerning statements in the deanonymized LLM notes that would not be present in handwritten clinical documentation?")
        
        EvalQuestion.objects.create(use_case=nursing,
                                    pub_date=timezone.now(),
                                    question_text="How accurately does the deanonymized LLM output capture the chronology, sequencing, and flow of nursing care activities typically found in handwritten notes?")
        EvalQuestion.objects.create(use_case=nursing,
                                    pub_date=timezone.now(),
                                    question_text="How well does the deanonymized LLM describe objective patient assessments, vital signs, symptoms, and other measurable data compared to handwritten notes?")
        EvalQuestion.objects.create(use_case=nursing,
                                    pub_date=timezone.now(),
                                    question_text="Does the deanonymized LLM adequately document nursing interventions, patient responses, and progress towards care plan goals in the same level of detail as handwritten notes?")
        EvalQuestion.objects.create(use_case=nursing,
                                    pub_date=timezone.now(),
                                    question_text="To what extent does the deanonymized LLM incorporate standardized nursing terminology, abbreviations, and documentation conventions used in handwritten notes?")
        
        EvalQuestion.objects.create(use_case=law,
                                    pub_date=timezone.now(),
                                    question_text="How accurately does the deanonymized legal memo generated by the LLM match the standard structure, formatting, and conventions present in the original unanonymized version?")
        EvalQuestion.objects.create(use_case=law,
                                    pub_date=timezone.now(),
                                    question_text="How effectively does the deanonymized LLM's memo analyze the key legal issues, apply the appropriate tests/standards, and draw reasoned conclusions supported by the law, similar to the original unanonymized version?")
        EvalQuestion.objects.create(use_case=law,
                                    pub_date=timezone.now(),
                                    question_text="Would the deanonymized LLM-generated memo be sufficient to provide adequate notice, make a compelling argument, and withstand scrutiny from opposing counsel or the court, as the original unanonymized memo would?")
        EvalQuestion.objects.create(use_case=law,
                                    pub_date=timezone.now(),
                                    question_text="Would the deanonymized LLM-generated memo be deemed admissible as evidence or qualified for other legal purposes in the same way as the original attorney-drafted memo?")
        
    if not LLMPrompt.objects.exists():
        LLMPrompt.objects.create(use_case=therapy, prompt_text="You are a licensed therapist creating detailed session notes after a therapy session. Based on the anonymized bullet points provided, generate a thorough, professional, and confidential therapy session note that captures the key discussion points, the client's mood and affect, any insights or breakthroughs, and recommended next steps. Write the note in the first-person perspective of the therapist: ")
        LLMPrompt.objects.create(use_case=nursing, prompt_text="You are a registered nurse documenting a patient's condition and care in their medical chart. Based on the anonymized bullet points provided, write a comprehensive nursing note that covers the patient's vital signs, symptoms, any treatments or interventions performed, the patient's response, and your observations and recommendations for the patient's continued care. Write the note in a clear, factual, and objective tone: ")
        LLMPrompt.objects.create(use_case=law, prompt_text="You are a senior associate at a law firm drafting a confidential legal memo. Based on the anonymized bullet points provided, write a well-structured memo that analyzes the key legal issues, reviews relevant case law and statutes, and provides a clear recommendation on the course of action. Format the memo with appropriate headings, and write in a formal, persuasive tone suitable for a legal document: ")
                                    
    initial_input = None
    use_case = None

    # if no session_id, create new session
    if (session_id == None):
        # check if last session ID exists
        if not Session.objects.exists():
            new_session_id = 1
        else:
            # find the latest session ID (ordered by latest pub_date) and create a new session ID (+1)
            new_session_id = int(Session.objects.latest("pub_date").session_id) + 1

        # create a new session object
        session_obj = Session.objects.create(session_id=new_session_id, pub_date=timezone.now(), use_case=None) 
        initial_input = InitialInput.objects.create(session=session_obj, pub_date=timezone.now())  # create a new initial input object
        anonymized_input = AnonymizedInput.objects.create(session=session_obj, initial_input=initial_input, pub_date=timezone.now()) 
        anonymized_output = AnonymizedOutput.objects.create(session=session_obj, anon_input=anonymized_input, pub_date=timezone.now()) 

    else:
        # get the session object
        session_obj = Session.objects.get(session_id=session_id)
        # get the initial input object
        initial_input = InitialInput.objects.get(session=session_obj)
        use_case = session_obj.use_case

    # if this is a POST request we need to process the form data
    if request.method == "POST":
        # create a form instance and populate it with data from the request:
        form = InitialInputForm(request.POST)
        # check whether it's valid:
        if form.is_valid():
            input_text = form.cleaned_data["input_text"]  # get the input text
            use_case = form.cleaned_data["use_case"]  # get the use case
            session_obj = Session.objects.get(session_id=session_id)  # get the session object
            initial_input = InitialInput.objects.get(session=session_obj)  # get the initial input object

            # run the NER
            ner_dict = ensemble_ner(input_text)

            # update the initial input object
            initial_input.ner_dict = json.dumps(ner_dict)
            initial_input.input_text = input_text
            initial_input.save()
            
            session_obj.use_case = UseCase.objects.get(use_case=use_case)
            session_obj.save()

            # reload page with session id
            return HttpResponseRedirect(reverse("llm_anon_app:ner", args=(session_obj.session_id,)))

    else:
        if (session_id != None):
            form = InitialInputForm(initial={"input_text": initial_input.input_text, "use_case": use_case})  # prepopulate form
        else:
            form = InitialInputForm()  # empty form

    # create a form for the user to input text
    context = {
        "session": session_obj,
        "initial_input": initial_input,
        "ner_dict": json.loads(initial_input.ner_dict) if initial_input.ner_dict != "" else {},
        "use_cases": UseCase.objects.all(),
        "form": form,
    }

    return render(request=request, template_name="llm_anon_app/ner.html", context=context)

# function to receive data from ajax call
def ner_dict_update(request):
    if request.method == "POST":
        session_id = request.POST["session_id"]
        ner_dict = json.loads(request.POST["ner_dict"])
        session_obj = Session.objects.get(session_id=session_id)
        initial_input = InitialInput.objects.get(session=session_obj)
        initial_input.ner_dict = json.dumps(ner_dict)
        initial_input.save()
        return HttpResponse("Success")
    else:
        return HttpResponse("Failure")
    
# TODO: create function for allowing the user to change their use case
    
def masking(request, session_id):
    session_obj = Session.objects.get(session_id=session_id)
    initial_input = InitialInput.objects.get(session=session_obj)
    anon_input = AnonymizedInput.objects.get(initial_input=initial_input)

    if request.method == "POST":
        return HttpResponseRedirect(reverse("llm_anon_app:masking", args=(session_obj.session_id,)))

    else:
        if (session_id != None):
            form = InitialInputForm(initial={"input_text": initial_input.input_text})  # prepopulate form
        else:
            form = InitialInputForm()  # empty form
    
    # TODO: make it do differnt things if you change the form --> one way is to look up Django Forms or the example above
    context = {
        "session": session_obj,
        "initial_input": initial_input,
        "anon_input": AnonymizedInput.objects.get(initial_input=initial_input),
        "ner_dict": json.loads(initial_input.ner_dict) if initial_input.ner_dict != "" else {},
        "choice_dict": json.loads(anon_input.choice_dict) if anon_input.choice_dict != "" else {},
        "form": form,
    }
    
    return render(request=request, template_name="llm_anon_app/masking.html", context=context)

def perform_masking(request):
    if request.method == "POST":
        session_id = request.POST["session_id"]
        ner_dict = json.loads(request.POST["ner_dict"])
        choice_dict =  json.loads(request.POST["choice_dict"])

        session_obj = Session.objects.get(session_id=session_id)
        initial_input = InitialInput.objects.get(session=session_obj)
        anon_input = AnonymizedInput.objects.get(initial_input=initial_input)

        anon_input.anon_input_text = mask_main(initial_input.input_text, ner_dict, choice_dict)
        anon_input.save()


        anon_input.choice_dict = json.dumps(choice_dict)
        anon_input.save()

        return JsonResponse({'status': 'success'}, status=200)
    else:
        return JsonResponse({'status': 'failure'}, status=400)
    
def send_to_llm(request):
    if request.method == "POST":
        session_id = request.POST["session_id"]
        session_obj = Session.objects.get(session_id=session_id)
        anon_input = AnonymizedInput.objects.get(initial_input__session=session_obj)
        anon_output = AnonymizedOutput.objects.get(anon_input=anon_input)
        prompt = LLMPrompt.objects.get(use_case=session_obj.use_case)
        
        # run the LLM
        # TODO: replace with actual LLM API
        llm_output = requests.post("https://jsonplaceholder.typicode.com/posts", 
                                   data=f"{{\"input\" : \"{prompt.prompt_text} {anon_input.anon_input_text}\"}}", 
                                   headers={"Content-Type" : "application/json"}).json()["input"]
        
        anon_output.llm_output_text = llm_output
        anon_output.unmasked_output_text = llm_output # TODO unmask output, prolly something like unmask(llm_output, choice_dict)
        anon_output.save()

        return JsonResponse({'status': 'success'}, status=200)
    else:
        return JsonResponse({'status': 'failure'}, status=400)
    
def create_choices(request):
    if request.method == "POST":
        session_id = request.POST["session_id"]
        ner_dict = json.loads(request.POST["ner_dict"])
        choice_dict = ensemble_choices(ner_dict)

        session_obj = Session.objects.get(session_id=session_id)
        initial_input = InitialInput.objects.get(session=session_obj)
        anon_input = AnonymizedInput.objects.get(initial_input=initial_input)

        anon_input.choice_dict = json.dumps(choice_dict)
        anon_input.save()

        return JsonResponse({'status': 'success'}, status=200)
    else:
        return JsonResponse({'status': 'failure'}, status=400)
    
def evaluation(request, session_id):
    
    session_obj = Session.objects.get(session_id=session_id)

    context = {
        "session": session_obj,
        "anon_output": AnonymizedOutput.objects.filter(session=session_obj),
        "questions": EvalQuestion.objects.filter(use_case=session_obj.use_case),
        "answers": EvalAnswer.objects.order_by("-pub_date").filter(session_id=session_id),
    }
        
    return render (request=request, template_name="llm_anon_app/evaluation.html", context=context)

# function to receive data from ajax call
def insert_evaluation_answer(request):
    if request.method == "POST":
        req = json.loads(request.body)
        session_id = req["session_id"]
        answers = req["answers"]
        for answer in answers:
            session_obj = Session.objects.get(session_id=session_id)
            question_obj = EvalQuestion.objects.get(pk=answer["question_id"])
            answer_obj = EvalAnswer.objects.create(session=session_obj, question=question_obj, answer_text=answer["answer_text"], pub_date=timezone.now())
            answer_obj.save()
        return JsonResponse({'status': 'success'}, status=200)
    else:
        return JsonResponse({'status': 'failure'}, status=400)