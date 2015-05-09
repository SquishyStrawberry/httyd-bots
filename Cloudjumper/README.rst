# cloudjumper  

Out of all of them, this is my favorite.  
Inspired from [Tmplt's Toothless](https://github.com/Tmplt/Toothless), it has all the same functionality and more.  

# Commands  

These are the commands that Cloudjumper can use, but these are not its methods.
For its methods, look in the docstrings.

## In-Channel  

Methods that can only be used in the channel, and not in private messages.
These methods assume that the bot's nick is Cloudjumper, but it could very well be anything else.

### Global  

#### Cloudjumper! roll (dice)  

Rolls an amount of dice with an amount of faces.  
Syntax for the dice is: [amount of dice, default is 1]d(amount of faces)

#### Cloudjumper! eat (person)  

Eats a certain person, who doesn't need to be connected.
The person is mandatory, and one person can't be eaten twice.

#### Cloudjumper! spit (person)

Spits out a certain person, who has to have been eaten.
The person is mandatory, again.

#### Cloudjumper! vomit

Equivalent to calling spit for all the people in Cloudjumper's stomach

#### Cloudjumper! stomach

Shows Cloudjumper's stomach, meaning all the people that have been eaten.

#### Cloudjumper! attack (person)

Attacks a person, who does not need to be connected.

### Whitelisted

#### Cloudjumper! learn (trigger) -> (response)

Learns (trigger), saying (response) every time (trigger) is in a message.

#### Cloudjumper! forget (trigger)

Forgets (trigger), meaning it won't respond with its (response) anymore.

### Admin

#### Cloudjumper! terminate

Stops the bot.