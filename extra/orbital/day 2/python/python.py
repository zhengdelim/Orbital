import random
low = 0
high = 100
guessed = False
secret = random.randint(low, high)

while not guessed:
    guess = input("Guess a number between " + repr(low) + "and" + repr(high) + ": ")
    if(guess < low or guess > high):
        print "STOP CHEATING!"

    elif (guess < secret):
        print "too low!"
        low = guess + 1

    elif (guess > secret):
        print "Too high!"
        high = guess - 1

    elif (guess == secret) :
        print "YAY!"
        guessed = True
    
        



