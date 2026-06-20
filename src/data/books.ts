import type { Book, SavedQuote } from '../types'

// NOTE ON TEXT:
// The reading sections below are original, copyright-safe prose written for this
// demo. They evoke the mood and structure of Kafka's "The Metamorphosis" — a man
// who wakes altered, the pressure of work, a family behind a door — without
// reproducing the actual novella. This keeps the MVP clean for distribution.

export const METAMORPHOSIS: Book = {
  id: 'metamorphosis',
  title: 'The Metamorphosis',
  author: 'Franz Kafka',
  year: '1915',
  tagline: 'A clerk wakes to find the shape of his life has changed overnight.',
  status: 'available',
  palette: {
    base: '#0c1411',
    accent: '#5f7a6b',
    glow: 'rgba(169, 196, 180, 0.22)',
    mood: 'Cold light · bureaucratic hush · quiet dread',
  },
  chapters: [
    {
      id: 'ch-1',
      title: 'I. The Morning Room',
      afterglow: {
        atmosphere:
          'A grey morning that never fully arrives. The room held its breath, the household kept its routines, and something enormous changed without permission. You spent this chapter inside a body and a building that no longer agree.',
        prompts: [
          'Where in your own life do you keep getting up at an alarm you no longer believe in?',
          'What would it cost you — really — to be unable to explain yourself to the people who depend on you?',
          'If a door stayed closed for one more hour, who on the other side would change first?',
        ],
      },
      sections: [
        {
          id: 's1',
          scene: 'Before the alarm',
          atmosphere: 'awakening',
          pullQuote:
            'He had been a person who travelled; now he was a person to whom things arrived.',
          paragraphs: [
            'The clerk woke before the alarm, which was unusual, and lay listening to a body that did not answer the way it used to. His thoughts were still tidy — schedules, the early train, the samples in their case — but his thoughts now sat at a strange distance from his limbs, the way a manager sits at a distance from the work.',
            'He had gone to sleep an ordinary man with debts and a ledger of small ambitions. He woke as something the morning had not consulted him about. He could feel the cold edge of the sheet, the grey of the ceiling, the long habit of duty pulling at him like a tide — and beneath all of it, a quiet, total wrongness he was not yet ready to name.',
            'For a while he simply waited, as one waits for a clerk at a counter, certain that the situation would be explained if he was only patient enough.',
          ],
          analysis: {
            happening:
              'A working man wakes to find his body unfamiliar and unresponsive. He does not panic — he reasons, as if the change were an administrative error that will be corrected.',
            keySymbol:
              'The unanswered alarm: time and duty continue on schedule even when the self can no longer keep up.',
            tension:
              'Between the orderly mind that still plans the workday and the altered body that quietly refuses it.',
            interpretation:
              'The opening asks what remains of a person when the usefulness that defined them is suddenly withdrawn. The horror is calm, procedural, almost polite.',
            remember:
              'He had been a person who travelled; now he was a person to whom things arrived.',
          },
        },
        {
          id: 's2',
          scene: 'The ceiling',
          atmosphere: 'ceiling',
          pullQuote: 'Duty does not pause to ask whether you are still shaped to carry it.',
          paragraphs: [
            'Above him the ceiling held its usual grey. He had looked at it a thousand mornings without seeing it, and now it seemed to look back — patient, institutional, the colour of a waiting room. Rain considered the window without committing to it.',
            'He thought of his employer, who measured men in minutes, and of the chief clerk who could turn a single late morning into a permanent suspicion. The thought arrived with its old force, but his body received it like a letter delivered to the wrong address.',
            'Somewhere in the flat a clock kept its small, indifferent accounting of the hour. Each tick was a coin laid on a counter he could no longer reach.',
          ],
          analysis: {
            happening:
              'He turns from his body to his obligations — the firm, the chief clerk, the train he is about to miss — measuring his crisis entirely in the currency of work.',
            keySymbol:
              'The clock: time as an accountant, charging interest on every minute he fails to perform.',
            tension:
              'Between private catastrophe and public expectation; no one outside the room yet knows anything is wrong.',
            interpretation:
              'Kafka locates dread not in monsters but in institutions. The most frightening presence in the room is a timetable.',
            remember: 'Duty does not pause to ask whether you are still shaped to carry it.',
          },
        },
        {
          id: 's3',
          scene: 'The window',
          atmosphere: 'window',
          pullQuote:
            'The world outside went on rehearsing a morning he was no longer cast in.',
          paragraphs: [
            'Through the window the street performed its ordinary overture: a cart, a cough, the wet shine of cobbles, a neighbour pulling a coat against the cold. The light came in flat and mineral, a green-grey light that belonged to ledgers and corridors rather than to mornings.',
            'He understood, distantly, that the world was continuing without adjusting itself to him in the slightest. This was not cruelty. It was simply the arrangement, the same arrangement that had always governed him, now revealed without its usual disguise of routine.',
            'The shadow of the window frame lay across the floor like the bars of a thing not yet called a cage.',
          ],
          analysis: {
            happening:
              'He looks outward at an indifferent street going about its business, and registers — without protest — that the world owes him no accommodation.',
            keySymbol:
              'The window frame’s shadow: an ordinary geometry that, at this angle, resembles bars.',
            tension:
              'Between belonging to the world and being quietly excused from it overnight.',
            interpretation:
              'The cage was always there; transformation only removes the wallpaper of habit that hid it. Freedom and confinement share the same frame.',
            remember:
              'The world outside went on rehearsing a morning he was no longer cast in.',
          },
        },
        {
          id: 's4',
          scene: 'The locked door',
          atmosphere: 'door',
          pullQuote: 'A family is sometimes only three people listening at the same door.',
          paragraphs: [
            'There were three voices now beyond the door, arranged at their familiar distances: his mother’s, soft and frightened into politeness; his father’s, heavy as a stamp pressed into wax; his sister’s, the youngest, hovering between them like a question no one had asked her to answer.',
            'They wanted him to open the door. He wanted, more than anything he had ever wanted at the office, to open the door — to walk out reasonable and recognised, to be received. But the lock was a small machine that required a hand, and he was learning, with a patience that frightened him, that he no longer had the hands the lock expected.',
            'So he spoke instead. And the sound that came out was almost his voice, almost, with something underneath it like furniture being dragged in another room.',
          ],
          analysis: {
            happening:
              'His family gathers outside the locked door, urging him to come out for work. He tries to comply and discovers his voice has changed beneath the words.',
            keySymbol:
              'The locked door: the thin partition between being a beloved son and an unexplained problem.',
            tension:
              'Love and obligation curdling into impatience; concern that is mostly fear of disruption.',
            interpretation:
              'Communication is the first thing to fail. When we cannot make ourselves understood, even devotion begins, gently, to withdraw.',
            remember: 'A family is sometimes only three people listening at the same door.',
          },
        },
        {
          id: 's5',
          scene: 'The chief clerk',
          atmosphere: 'office',
          pullQuote:
            'The firm sent a man to the house, the way one sends a notice to a debtor.',
          paragraphs: [
            'The firm had sent the chief clerk himself, which meant the matter was already serious, already filed. The man’s voice came through the door dressed in the particular courtesy that precedes an accusation: an inquiry after one’s health that is really an audit.',
            'There were hints of complaints, of accounts not entirely in order, of a confidence that had perhaps been misplaced. The clerk understood that he was being dismantled in his own hallway, item by item, by a representative of the only institution that had ever defined him.',
            'He gathered everything he was and pressed it toward speech — an explanation, a defence, a single clear sentence — and what crossed the threshold was a sound that emptied the corridor of everyone in it.',
          ],
          analysis: {
            happening:
              'A senior representative of the firm arrives to interrogate the clerk’s absence through the door, layering professional threat over private crisis.',
            keySymbol:
              'The chief clerk: the institution given a face, arriving to collect on a man as if on an overdue account.',
            tension:
              'Maximum pressure — the workplace invades the home at the exact moment he is least able to perform.',
            interpretation:
              'Worth measured purely in output is worth that can be revoked. The visit dramatises how quickly a valued employee becomes a liability.',
            remember: 'The firm sent a man to the house, the way one sends a notice to a debtor.',
          },
        },
        {
          id: 's6',
          scene: 'The threshold',
          atmosphere: 'threshold',
          pullQuote: 'To be seen at last, and to watch being seen become recoiling.',
          paragraphs: [
            'When the door finally gave — when the lock surrendered to an effort that cost him more than he knew he had — the hallway received him in full daylight, and for one suspended moment he was simply present, visible, returned to his family and the world.',
            'Then he watched the recognition leave their faces. He watched the chief clerk’s courtesy collapse into instinct, watched his mother reach for the table, watched his father’s hand rise — not in greeting. The moment of being seen and the moment of being feared were, he realised, the same moment, with nothing in between.',
            'He had crossed the threshold he had longed to cross. It turned out that the threshold was not a door but a verdict.',
          ],
          analysis: {
            happening:
              'The door opens and the family sees him for the first time since the change. Their reaction is immediate, physical recoil rather than understanding.',
            keySymbol:
              'The threshold: the line between concealment and exposure, crossed only once and never recrossed.',
            tension:
              'The unbearable gap between how he experiences himself and how he is now perceived.',
            interpretation:
              'Identity is not only what we are but what others agree to keep seeing. To be misrecognised by those who love us is its own transformation.',
            remember: 'To be seen at last, and to watch being seen become recoiling.',
          },
        },
        {
          id: 's7',
          scene: 'The retreat',
          atmosphere: 'corridor',
          pullQuote:
            'He learned the geography of a single room the way the exiled learn a country.',
          paragraphs: [
            'He was driven back — gently in intention, brutally in effect — into the room that had been only a bedroom and was now becoming something else. The door closed. The lock, which had defeated him, now did its work easily from the other side.',
            'In the hours that followed he began, without deciding to, to learn the room differently: the cool of the floor, the angle of the wall, the small territories of shadow that the cold light left untouched. The man who had measured cities by their train stations now measured the distance from the bed to the window in a currency he was only beginning to understand.',
            'Behind the wall the household reorganised itself around his absence with a speed that would have wounded him, had he still been entirely the one to be wounded.',
          ],
          analysis: {
            happening:
              'He is forced back into his room and the door is shut behind him. He begins, almost tenderly, to adapt to a drastically smaller world.',
            keySymbol:
              'The room: a shrinking territory that becomes, by necessity, an entire country.',
            tension:
              'Between the family’s relief at containment and his dawning, lonely competence in confinement.',
            interpretation:
              'Adaptation can be a quiet tragedy. We are capable of making a home out of almost any reduction — and that capacity is exactly what lets the world reduce us.',
            remember:
              'He learned the geography of a single room the way the exiled learn a country.',
          },
        },
        {
          id: 's8',
          scene: 'Dust in the light',
          atmosphere: 'dust',
          pullQuote:
            'The light did not judge him. It only fell, as light does, on whatever happened to be there.',
          paragraphs: [
            'By afternoon the room had settled into a stillness that was almost peace. Dust turned slowly in the one shaft of light that reached the floor, each particle rising and falling on currents too faint for any window to explain.',
            'He found that if he kept very still he could watch the dust for a long time, and that the watching asked nothing of him — no schedule, no explanation, no defence. It was the first thing in his entire life, he realised, that had ever simply let him be present without first requiring him to be useful.',
            'Somewhere a clock went on counting. But here, in the slow gold of the falling dust, the counting belonged to a country he had quietly, and not unwillingly, begun to leave.',
          ],
          analysis: {
            happening:
              'Alone and still, he watches dust drift in a shaft of light and experiences, unexpectedly, something close to rest.',
            keySymbol:
              'Dust in sunlight: weightless, purposeless, beautiful — everything the world of work refused to let him be.',
            tension:
              'Between the grief of his exile and a strange, unearned serenity within it.',
            interpretation:
              'The chapter closes not on horror but on a fragile stillness. When usefulness is stripped away, what remains can be loss — and, briefly, a terrible kind of freedom.',
            remember:
              'The light did not judge him. It only fell, as light does, on whatever happened to be there.',
          },
        },
      ],
    },
  ],
}

export const CRIME_AND_PUNISHMENT: Book = {
  id: 'crime-and-punishment',
  title: 'Crime and Punishment',
  author: 'Fyodor Dostoevsky',
  year: '1866',
  tagline: 'A feverish mind paces a candlelit city, rehearsing a deed it cannot undo.',
  status: 'coming-soon',
  palette: {
    base: '#160a0c',
    accent: '#7a1f24',
    glow: 'rgba(232, 168, 92, 0.22)',
    mood: 'Candlelight · snow · psychological heat',
  },
  chapters: [],
}

export const NINETEEN_EIGHTY_FOUR: Book = {
  id: '1984',
  title: '1984',
  author: 'George Orwell',
  year: '1949',
  tagline: 'A clerk of the future edits the past while a poster watches him do it.',
  status: 'coming-soon',
  palette: {
    base: '#101113',
    accent: '#c8302b',
    glow: 'rgba(183, 188, 194, 0.18)',
    mood: 'Brutalist grey · red warning · constant surveillance',
  },
  chapters: [],
}

export const BOOKS: Book[] = [
  METAMORPHOSIS,
  CRIME_AND_PUNISHMENT,
  NINETEEN_EIGHTY_FOUR,
]

// A few pre-populated quotes so the Saved Quotes drawer feels alive on first open.
export const SEED_QUOTES: SavedQuote[] = [
  {
    id: 'seed-1',
    text: 'He had been a person who travelled; now he was a person to whom things arrived.',
    bookTitle: 'The Metamorphosis',
    author: 'Franz Kafka',
    source: 'Before the alarm',
    savedAt: Date.now() - 1000 * 60 * 60 * 26,
  },
  {
    id: 'seed-2',
    text: 'A family is sometimes only three people listening at the same door.',
    bookTitle: 'The Metamorphosis',
    author: 'Franz Kafka',
    source: 'The locked door',
    savedAt: Date.now() - 1000 * 60 * 60 * 3,
  },
  {
    id: 'seed-3',
    text: 'The world outside went on rehearsing a morning he was no longer cast in.',
    bookTitle: 'The Metamorphosis',
    author: 'Franz Kafka',
    source: 'The window',
    savedAt: Date.now() - 1000 * 60 * 40,
  },
]
