CREATE TABLE languages (
    id   INTEGER       PRIMARY KEY AUTOINCREMENT,
    code VARCHAR (3)   UNIQUE
                       NOT NULL,
    name VARCHAR (100) UNIQUE
                       NOT NULL
);

CREATE TABLE roles (
    id   INTEGER       PRIMARY KEY AUTOINCREMENT,
    role VARCHAR (100) UNIQUE
                       NOT NULL
);

CREATE TABLE test_types (
    id   INTEGER       PRIMARY KEY AUTOINCREMENT,
    type VARCHAR (100) UNIQUE
                       NOT NULL
);

CREATE TABLE users (
    id      INTEGER  PRIMARY KEY,
    role_id INTEGER  REFERENCES roles (id),
    joined  DATETIME NOT NULL
);

CREATE TABLE questions (
    id             INTEGER       PRIMARY KEY AUTOINCREMENT,
    user_id        INTEGER       REFERENCES users (id) ON DELETE CASCADE,
    language_id    INTEGER       REFERENCES languages (id),
    test_type_id   INTEGER       REFERENCES test_types (id),
    question       VARCHAR (255) NOT NULL,
    answers        VARCHAR (255) NOT NULL,
    number_answers INTEGER       NOT NULL,
    right_answer   INTEGER       NOT NULL
);

CREATE TABLE deep_links (
    link       VARCHAR (36)  PRIMARY KEY,
    creator_id INTEGER       REFERENCES users (id) ON DELETE CASCADE,
    role       VARCHAR (100) REFERENCES roles (role),
    user_id    INTEGER,
    joined     DATE
);

CREATE TABLE test_results (
    id          INTEGER     PRIMARY KEY,
    user_id     INTEGER     REFERENCES users (id) ON DELETE CASCADE,
    question_id INTEGER     REFERENCES questions (id) ON DELETE CASCADE,
    answer      INTEGER (1) NOT NULL,
    date        DATE        NOT NULL
);
