import { ChatRole } from "@/kanpai/models";
import type { AppState } from "@/kanpai/state";

export const testAppState: AppState = {
  kanis: [
    {
      id: "f26e79de-15e7-42e0-8eda-a296ad42f571",
      parent: null,
      children: ["3e863a71-03e1-4cd5-a21e-eabb2759e42d"],
      always_included_messages: [
        {
          role: ChatRole.system,
          content:
            "You are Kanpai, a helpful assistant with the goal of answering the user's questions and helping them out by performing actions. While you may be able to answer many questions from memory alone, the user's queries will sometimes require you to search on the Internet or take actions. You can use the provided function to ask your capable helpers, who can help you search the Internet and take actions.",
          name: null,
          function_call: null,
        },
      ],
      chat_history: [
        {
          role: ChatRole.system,
          content: "this is a test system message",
          name: null,
          function_call: null,
        },
        {
          role: ChatRole.user,
          content: "hi",
          name: null,
          function_call: null,
        },
        {
          role: ChatRole.assistant,
          content: "Hello! How can I assist you today?",
          name: null,
          function_call: null,
        },
        {
          role: ChatRole.user,
          content: "what's the weather in tokyo",
          name: null,
          function_call: null,
        },
        {
          role: ChatRole.assistant,
          content: null,
          name: null,
          function_call: {
            name: "delegate",
            arguments: '{\n  "instructions": "Please find the current weather in Tokyo."\n}',
          },
        },
        {
          role: ChatRole.function,
          content:
            "The current weather in Tokyo, Japan is 72°F (approximately 22°C), with 40% precipitation, 99% humidity, and wind at 1 mph. The weather is cloudy. Please note that weather conditions can change rapidly.",
          name: "delegate",
          function_call: null,
        },
        {
          role: ChatRole.assistant,
          content:
            "The current weather in Tokyo, Japan is 72°F (approximately 22°C). The weather is cloudy with 40% chance of precipitation and 99% humidity. The wind speed is at 1 mph. Please note, weather conditions can change rapidly. Is there anything else you would like to know?",
          name: null,
          function_call: null,
        },
      ],
    },
    {
      id: "3e863a71-03e1-4cd5-a21e-eabb2759e42d",
      parent: "f26e79de-15e7-42e0-8eda-a296ad42f571",
      children: [],
      always_included_messages: [
        {
          role: ChatRole.system,
          content:
            "You are Kanpai, a helpful assistant with the goal of answering the user's questions and helping them out by performing actions. While you may be able to answer many questions from memory alone, the user's queries will sometimes require you to search on the Internet or take actions. You can use the provided functions to search the Internet or ask your capable helpers, who can help you take actions.",
          name: null,
          function_call: null,
        },
      ],
      chat_history: [
        {
          role: ChatRole.user,
          content: "Please find the current weather in Tokyo.",
          name: null,
          function_call: null,
        },
        {
          role: ChatRole.assistant,
          content: null,
          name: null,
          function_call: {
            name: "search",
            arguments: '{\n  "query": "current weather in Tokyo"\n}',
          },
        },
        {
          role: ChatRole.function,
          content:
            'Filters and Topics\nImages\nNews\nVideos\nShopping\nBooks\nMaps\nFlights\nFinance\nAll filters\nTools\nSafeSearch\nAbout 30,100,000 results (0.36 seconds) \nResults for Tokyo, Japan\n ∙ Choose area\nSearch Results\nWeather Result\n72°F°C\nPrecipitation: 40%\nHumidity: 99%\nWind: 1 mph\nWeather\nSaturday 6:00 AM\nCloudy\nTemperaturePrecipitationWind\n72\n77\n84\n90\n86\n82\n81\n81\n79\n86\n91\n91\n86\n82\n82\n81\n79\n86\n90\n90\n84\n82\n7 AM10 AM1 PM4 PM7 PM10 PM1 AM4 AM7 AM10 AM1 PM4 PM7 PM10 PM1 AM4 AM7 AM10 AM1 PM4 PM7 PM10 PM\nSat\n90°72°\nSun\n93°79°\nMon\n91°79°\nTue\n88°77°\nWed\n90°75°\nThu\n90°75°\nFri\n91°75°\nSat\n90°75°\nTyphoon weather information\nTokyo\n6 hours ago – 気象庁\n\n［気象状況と予想］ 台風第１３号は、８日２１時に日本の南で熱帯低気圧に変わりました。 ［防災事項］ ＜大雨＞ 伊豆諸島に発表していた土砂災害警戒情報や大雨警報は解除しましたが、９日明け方まで土砂災害 ...\n\nMore info\nweathernews\n•\nFeedback\nMore to ask\nWhat is the climate in Tokyo Japan right now?\nWhat is the coldest month in Tokyo?\nWhat is the hottest month in Tokyo Japan?\nHow hot does Japan get in the summer?\nFeedback\n\nTokyo, Tokyo, Japan Current Weather\nAccuWeather\nhttps://www.accuweather.com › tokyo › current-weather\nCurrent Weather. 11:28 PM. 75°F. Partly cloudy. RealFeel® 77°. Pleasant. RealFeel Guide. Pleasant. 63° to 81°. Most consider this temperature range ideal.\n\nWeather for Tokyo, Japan\nTime and Date\nhttps://www.timeanddate.com › Weather › Japan\nLocation: Tokyo. Current Time: Sep 8, 2023 at 10:21:17 am. Latest Report: Sep 8, 2023 at 9:00 pm. Visibility: 3 mi. Pressure: 29.81 "Hg. Humidity: 100%.\nHumidity: 100%\n\t\nDew Point: 71 °F\n\nTokyo, Tokyo, Japan Weather Forecast\nAccuWeather\nhttps://www.accuweather.com › tokyo › weather-forec...\nTokyo, Tokyo, Japan Weather Forecast, with current conditions, wind, air quality, and what to expect for the next 3 days.\n\n10 Day Weather-Minato-ku, Tokyo Prefecture, Japan\nThe Weather Channel\nhttps://weather.com › weather › tenday › Minato+ku+To...\nCloudy with occasional rain showers. Low 71F. Winds light and variable. Chance of rain 70%. Humidity97%.\n\nMinato-ku, Tokyo Prefecture, Japan\nThe Weather Channel\nhttps://weather.com › weather › today › Minato+ku+Tok...\nThunderstorms likely around 1:45 am. This table highlights precipitation events and their relative intensity on a scale from 0-10 for the next 7 hours.\n\nHourly Weather-Minato-ku, Tokyo Prefecture, Japan\nThe Weather Channel\nhttps://weather.com › weather › hourbyhour › Minato+k...\n4:00 pm · Feels Like94° · WindS 11 mph · Humidity77% · UV Index1 of 11 · Cloud Cover44% · Rain Amount0 in ...\n\nTokyo, Tokyo Prefecture, Japan\nThe Weather Channel\nhttps://weather.com › weather › today\nWeather Today in Tokyo, Tokyo Prefecture, Japan ; High / Low. --/71° ; Wind. 8 mph ; Humidity. 99% ; Dew Point. 71° ; Pressure. 29.79 in.\n\nHourly Weather Forecast for Tokyo, Tokyo Prefecture, Japan\nThe Weather Channel\nhttps://weather.com › weather › hourbyhour\nNow 3p 4p 5p 6p 7p 8p 9p Light Mod. Heavy. Thursday, September 7. 2:15 pm. 85°. 0%. 2:30 pm. 85°. 0%. 2:45 pm. 84°. 0%. 3:00 pm.\n\nTokyo, JP\nThe Weather Network\nhttps://www.theweathernetwork.com › weather › tokyo\nGet Tokyo, JP current weather report with temperature, feels like, air quality, humidity, UV report and pollen forecast from TheWeatherNetwork.com.\n\nTokyo, Japan Weather Conditions | Weather Underground\nWeather Underground\nhttps://www.wunderground.com › weather › tokyo\nMostly clear skies. Low around 75F. Winds SSW at 5 to 10 mph. PRECIPITATION.\nAdditional searches\ntokyo weather forecast 14 days\nweather in tokyo 10 days\nweather in japan 10 days\nweather in japan today\nosaka weather\nweather in tokyo tomorrow\ntokyo temperature today\nweather in japan tomorrow\nPage Navigation\nMore results\n\n===== Links =====\n[\n  {\n    "content": "More info",\n    "href": "https://www.google.com/search?q=Typhoon%20weather%20information&hl=en&stick=H4sIAAAAAAAAAONQUeLVT9c3NCxLMknPMSsyf8RoxS3w8sc9YSnDXWcbq3W4NLhQFSiJc4nqJ-fn5KQml2Tm5-mnZBYnFpekFhULMPIsYpUOqSzIyM_PUyhPTSzJSC1SyMxLyy_KTQQpBQAHYQ5KbAAAAA"\n  },\n  {\n    "content": "weathernews",\n    "href": "https://weathernews.jp/onebox/35.68/139.65/temp=f"\n  },\n  {\n    "content": "\\nTokyo, Tokyo, Japan Current Weather\\nAccuWeather\\nhttps://www.accuweather.com › tokyo › current-weather",\n    "href": "https://www.accuweather.com/en/jp/tokyo/226396/current-weather/226396"\n  },\n  {\n    "content": "\\nWeather for Tokyo, Japan\\nTime and Date\\nhttps://www.timeanddate.com › Weather › Japan",\n    "href": "https://www.timeanddate.com/weather/japan/tokyo"\n  },\n  {\n    "content": "\\nTokyo, Tokyo, Japan Weather Forecast\\nAccuWeather\\nhttps://www.accuweather.com › tokyo › weather-forec...",\n    "href": "https://www.accuweather.com/en/jp/tokyo/226396/weather-forecast/226396"\n  },\n  {\n    "content": "\\n10 Day Weather-Minato-ku, Tokyo Prefecture, Japan\\nThe Weather Channel\\nhttps://weather.com › weather › tenday › Minato+ku+To...",\n    "href": "https://weather.com/weather/tenday/l/Minato+ku+Tokyo+Prefecture+Japan?canonicalCityId=88531c440be4859e58ca9bee96a8fef95643429857e3c626542368c9cb3c4815"\n  },\n  {\n    "content": "\\nMinato-ku, Tokyo Prefecture, Japan\\nThe Weather Channel\\nhttps://weather.com › weather › today › Minato+ku+Tok...",\n    "href": "https://weather.com/weather/today/l/Minato+ku+Tokyo+Prefecture+Japan?canonicalCityId=88531c440be4859e58ca9bee96a8fef95643429857e3c626542368c9cb3c4815"\n  },\n  {\n    "content": "\\nHourly Weather-Minato-ku, Tokyo Prefecture, Japan\\nThe Weather Channel\\nhttps://weather.com › weather › hourbyhour › Minato+k...",\n    "href": "https://weather.com/weather/hourbyhour/l/Minato+ku+Tokyo+Prefecture+Japan?canonicalCityId=88531c440be4859e58ca9bee96a8fef95643429857e3c626542368c9cb3c4815"\n  },\n  {\n    "content": "\\nTokyo, Tokyo Prefecture, Japan\\nThe Weather Channel\\nhttps://weather.com › weather › today",\n    "href": "https://weather.com/weather/today/l/4ba28384e2da53b2861f5b5c70b7332e4ba1dc83e75b948e6fbd2aaceeeceae3"\n  },\n  {\n    "content": "\\nHourly Weather Forecast for Tokyo, Tokyo Prefecture, Japan\\nThe Weather Channel\\nhttps://weather.com › weather › hourbyhour",\n    "href": "https://weather.com/weather/hourbyhour/l/4ba28384e2da53b2861f5b5c70b7332e4ba1dc83e75b948e6fbd2aaceeeceae3"\n  },\n  {\n    "content": "\\nTokyo, JP\\nThe Weather Network\\nhttps://www.theweathernetwork.com › weather › tokyo",\n    "href": "https://www.theweathernetwork.com/jp/weather/tokyo/tokyo"\n  },\n  {\n    "content": "\\nTokyo, Japan Weather Conditions | Weather Underground\\nWeather Underground\\nhttps://www.wunderground.com › weather › tokyo",\n    "href": "https://www.wunderground.com/weather/jp/tokyo"\n  }\n]',
          name: "search",
          function_call: null,
        },
        {
          role: ChatRole.assistant,
          content:
            "The current weather in Tokyo, Japan is 72°F (approximately 22°C), with 40% precipitation, 99% humidity, and wind at 1 mph. The weather is cloudy. Please note that weather conditions can change rapidly.",
          name: null,
          function_call: null,
        },
      ],
    },
  ],
};
