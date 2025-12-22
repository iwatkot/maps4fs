# The Origin Story of Maps4FS

I've told this story before, but I think it deserves to be told all at once in one place.

## The Beginning

I've been playing Farming Simulator since FS13, and I never liked the built-in maps. They feel toyish and unrealistic somehow—like something out of Fortnite. Community-made maps aren't much better either, because they're created in random places that mean nothing to me personally.

At some point, I decided: "I'm going to create my own map based on a real location. The FS community is huge and the game is incredibly popular. There must be dozens of various tools available to do this. I figured I'd sit back and pick the best generator tool."

So I went to Google and found... nothing.

## The Search

I turned to YouTube and found tutorials where creators have Giants Editor open on one side and Google Maps on the other, manually drawing maps pixel by pixel. I thought, "There has to be something better than this."

Then I found people who paint directly over satellite images in Giants Editor. But first, you have to spend twenty minutes downloading the image. Some tutorials promise downloading DEM images in "less than an hour"—and that's not even a joke. That's when it hit me: I'm incredibly lazy, and there's no way I'm spending 50+ hours drawing a map manually.

I went to Reddit and asked if there was really no automation tool for this. I remembered that back when I played Cities in Motion, there was a tool called Maps4CIM (which is where I got the naming idea—maps4fs is built on the concepts of that project). But the FS community told me nothing like that exists. I was shocked and almost gave up on the idea.

Then I thought: "Well, there's Giants Editor. Let me see how it actually works."

## The Investigation

And so the investigation began. I spent time trying to understand how map files work. When I finally grasped how it all fit together, I started researching DTM, geospatial data, and coordinate systems—topics I knew almost nothing about.

To be honest, my knowledge was so bad that I was manually calculating coordinates in my code instead of using ready-made libraries. This decision came back to haunt me later when the project grew and I discovered these weird, incorrect conversions from my earliest coding attempts.

## The First Version

Eventually, I created a simple script, wrapped it so others could use it (no fancy interface), and posted a video on YouTube. I also created a Telegram bot. Then... silence. It was peaceful, actually—I was playing my custom map, nobody was using the tool, and life went on.

But then some people started contacting me about it.

## The Turning Point

As FS25 approached, I remember sitting in the FS Discord, waiting for Giants Editor 10 to be released so I could add FS25 support (it only worked for FS22 at the time). Some people in the community suggested, "You should make a Discord server." I thought, "Who the hell needs that?"

Turns out, the community really did need it.

## The Real Insight

Looking back now, I think it's a closed loop: it's not that community members don't *want* to create their own maps, it's just that it's too difficult for most people. So they don't do it. But when there's a tool that makes it easier, surprisingly (or not surprisingly), map creation becomes more popular.

The path has been painful for me, mainly because I had zero experience in FS modding. I had no idea how to work with meshes or any of that. During development, I had to learn everything from scratch—understand how things work, and simultaneously try to explain it to others who were using the tool before I'd even fully mastered it myself.

## The Goal

That's how maps4fs came to be, and I hope it helps people like myself create maps from the places we care about and play on them. Eventually, if the community's demand is clear enough, maybe someone (hey, Giants!) can build something completely automated and easy for everyone.

For me, it was never about personal interest, fame, or ego. In the end, I just want to play Farming Simulator in a place I care about, and I hope that maps4fs has helped the community with that.
