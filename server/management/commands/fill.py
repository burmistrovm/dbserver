from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User
from ask.models import Question, Answer, Tags

class Command(BaseCommand):
	help = 'Fill the database'
	def handle(self, *args, **options):
		User.objects.all().delete()
		user = User.objects.create_user("nuf","nuf@nuf.ru","nuf")
		user.save()
		tagmas = ['ActionScript', 'Ada', 'Bash', '(Visual) Basic', 'Bourne Shell', 'Bro', 'C', 'C Shell', 'C#', 'C++', 'Curl', 'Fortran', 'Go', 'Haskell', 'Java', 'JavaScript', 'Lisp', 'Maple', 'Mathematica', 'MATLAB', 'MOO', 'Objective-C', 'Pascal', 'Perl', 'PHP', 'Python', 'Ruby', 'Simulink', 'Verilog', 'VHDL']
		Question.objects.all().delete()
		Tags.objects.all().delete()
		for i in range(1,10):
			q = Question(
				author = user, 
				text = 'In eget neque in turpis suscipit tristique vitae nec mauris. Vestibulum auctor, turpis non lobortis gravida, nisi est vulputate lectus, ut dictum erat augue ut erat.',
				title = 'title' + str(i),
				question_id = i,
				)
			q.save()
			t1 = Tags(
				name = tagmas[(i-1)*2]
				)
			t2 = Tags(
				name = tagmas[(i-1)*2+1]
				)
			t1.save()
			t2.save()
			t1.question.add(q)
			t2.question.add(q)
			for j in range(1,10):
				a = Answer(
					text = 'In eget neque in turpis suscipit tristique vitae nec mauris. Vestibulum auctor, turpis non lobortis gravida, nisi est vulputate lectus, ut dictum erat augue ut erat. In fringilla tincidunt dolor, at pulvinar lacus cursus nec. Pellentesque ultrices eget odio ac ullamcorper. Duis turpis orci, tempor vel massa id, posuere condimentum purus. Sed rutrum magna non nisi posuere interdum. Vivamus eget diam dictum mi malesuada accumsan.',
					author = user,
					question = q,
					)
				a.save()
