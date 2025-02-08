# conway-s_music_of_life
 experimenting_with audio version of conway's GoL


202501211548

i'm quite proud of this one if i do say so myself. after previous experiments into playing with first code to calculate which basic cellular automata were amphichiral, i then digressed into actually coding scripts to generate cellular automata, then conway's game of life - and then it hit me - what if, instead of generating graphical output, i had it output sound? what would it sound like to hear the spaceships, birds, oscillators and other 'lifeforms'?  what would the general hum of continuous birth, growthl, division and death sound like?

i set it to play different pitches depending on how many live 'cells' were neighbouring the cell in question, and play different volumes depending similarly but on neighbouring cells touching on the y-axis instead of x-axis. this was an idea inspired by previous investigations into making the traditional bicolour GoL instead have a whole depth of colour-field based on number of neighbouring cells.

the original output was, admittedly somehwat cacophonouus - yet even then instantly engaging and excfiting. and somehow surprisingly appealing. it was fascinating how you could hear different oscillators form, alternate steadily back and forth between two notes for as loing as they rmeained stable and alive, whilst other sounds, clearly spaceships or birds etc. would be little wobbling melodies or looping patterns that would gradually climb or descend in pich as they did the equivalent of whwat would have been flying across the field of view had it been graphical.

next was another stroke of genius - quantization.
by setting the code to only output notes rounded to pitches set at frequencies corresponding to a set range of whole notes, it began to output actual tonal music - it was now a tune generator and even began to produce chords!
i progressed further to setting up a choice of scales for the quantizer and so could have not just major but minor, pentatonic, blues and more as choices - this really enhanced the output, making the melodies and chord sequrences generated particularly haunting or uplifting or many other things besides - there was real emotion in it now!

i haven't really returned to it since this intial investigation but this is a most spectacularly promising endeavour and needs not only to be investigated further but also i think other forms of cellular automata and similar mathematical generators need to be similarly setup.