# OpenPostbud KMD Nova journalisering

## Intro

This robot is used to journalise shipments made in OpenPostbud to KMD Nova.

The robot is started using a OS2Forms form at [found here.](https://selvbetjening.aarhuskommune.dk/da/form/rpa-openpostbud-journalisering-i)

## Process arguments

The robot expects a json string in the following format:

```json
{
    "accepted_azs": [
        "az123456789"
    ]
}
```

__accepted_azs__: A list of user AZs which are whitelisted to use the robot.
