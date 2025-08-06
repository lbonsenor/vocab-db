# VocabDB

> **Made by**: Lautaro Bonseñor
>
> A tool for learning a language with Database Management

> [!note]
>
> ## What are Lexemes and Morphemes?
>
> A **lexeme** is the abstract unit representing all inflected forms of a single forms. In Layman's terms, the dictionary form of a word.
>
> A **morpheme** is the smallest linguistic component of meaning.
>
> As an example: the word `cats` consists of two morphemes: `cat` and `-s`, yet both cat and cats are considered part of the same lexeme.

> [!note]
>
> ## What are POS (Parts of Speech) / UPOS / XPOS ?
>
> `POS` is a grammatical cateogry to which a word is assigned in accordance with its syntactic functions, i.e: noun, pronoun, adjective, verb, etc.
>
> `UPOS` tags are the `POS` annotations used in Universal Dependencies, which is a framework for consistent annotation of grammar across all languages, i.e: NOUN, ADJ, VERB, PRON
>
> `XPOS` tags are language-specific `POS` annotations, which are not precisely defined by the UD standard
>
> Both `UPOS` and `XPOS` are used by the **_Stanza Python NLP Package_** in order to recognize parts of speech and entities, do syntactic analysis, and more.

> [!important]
>
> ## Package Requirements
>
> A **Python** virtual environment (venv)
>
> ```sh
> # macOS/Linux
> # You may need to run `sudo apt-get install python3-venv` first on Debian-based OSs
> python3 -m venv .venv
>
> # Windows
> # You can also use `py -3 -m venv .venv`
> python -m venv .venv
> ```
>
> **Jupyter**, **Stanza**, and **PostgreSQL** packages
>
> ```sh
> pip install jupyter stanza python-dotenv psycopg2
> ```

> [!important]
>
> ## Environment Variables
>
> Add the following variables to your `.env` file
>
> ```py
> user = [YOUR_POSTGRESQL_USR]
> password = [YOUR_POSTGRESQL_PASSWD]
> host = [YOUR_POSTGRESQL_HOST]
> port = [YOUR_POSTGRESQL_PORT]
> dbname = [YOUR_POSTGRESQL_DBNAME]
> ```

## Tables

|                       |    **lemmas**     |                        |
| :-------------------: | :---------------: | ---------------------- |
| word_id: `PK FK uuid` | index: `PK int8 ` | morpheme_id: `FK uuid` |

|               |              | **words**          |                     |
| :-----------: | :----------: | ------------------ | ------------------- |
| id: `PK uuid` | text: `text` | upos_id: `FK uuid` | translation: `text` |

|               |              | **morphemes**      |                     |
| :-----------: | :----------: | ------------------ | ------------------- |
| id: `PK uuid` | text: `text` | xpos_id: `FK uuid` | translation: `text` |

| **upos_tags** |               |
| :-----------: | :-----------: |
| id: `PK text` | label: `text` |

| **xpos_tags** |               |
| :-----------: | :-----------: |
| id: `PK text` | label: `text` |
