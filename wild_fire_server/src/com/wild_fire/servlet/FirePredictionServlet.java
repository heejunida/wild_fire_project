package com.wild_fire.servlet;

import javax.servlet.ServletException;
import javax.servlet.annotation.WebServlet;
import javax.servlet.http.HttpServlet;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;
import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStreamReader;
import java.io.PrintWriter;
import java.util.stream.Collectors;

// This servlet responds to the /fire-predict URL called by the JavaScript
@WebServlet("/fire-predict1")
public class FirePredictionServlet extends HttpServlet {
    protected void doGet(HttpServletRequest request, HttpServletResponse response)
            throws ServletException, IOException {

        // 1. Get lat/lon parameters from the request
        String lat = request.getParameter("lat");
        String lon = request.getParameter("lon");

        // Validate parameters
        if (lat == null || lon == null || lat.isEmpty() || lon.isEmpty()) {
            response.setStatus(HttpServletResponse.SC_BAD_REQUEST);
            response.getWriter().write("{\"error\": \"Missing lat/lon parameters.\"}");
            return;
        }

        // 2. Define the path to the prediction script
        String pythonScriptPath = "/Users/heejunida/wild_fire_project/wild_fire_client/predict_fire_spread.py";
        String pythonExecutable = "python3";

        // 3. Prepare the command to execute the Python script
        ProcessBuilder pb = new ProcessBuilder(
            pythonExecutable,
            pythonScriptPath,
            "--lat", lat,
            "--lon", lon
        );

        pb.redirectErrorStream(true);

        try {
            // 4. Execute the process
            Process process = pb.start();

            // 5. Read all output from the script
            String scriptOutput;
            try (BufferedReader reader = new BufferedReader(new InputStreamReader(process.getInputStream()))) {
                scriptOutput = reader.lines().collect(Collectors.joining(System.lineSeparator()));
            }

            // 6. Wait for the script to finish
            int exitCode = process.waitFor();

            // 7. Set up the HTTP response
            response.setContentType("application/json");
            response.setCharacterEncoding("UTF-8");
            PrintWriter out = response.getWriter();

            if (exitCode == 0) {
                // Find the start of the GeoJSON in the script's output.
                // We'll look for the first '{' since the JSON is the last thing printed.
                int jsonStartIndex = scriptOutput.indexOf('{');
                if (jsonStartIndex != -1) {
                    String geoJson = scriptOutput.substring(jsonStartIndex);
                    out.print(geoJson);
                } else {
                    response.setStatus(HttpServletResponse.SC_INTERNAL_SERVER_ERROR);
                    out.print("{\"error\": \"Could not parse GeoJSON from script output.\", \"details\": \"" + scriptOutput.replace("\"", "'") + "\"}");
                }
            } else {
                response.setStatus(HttpServletResponse.SC_INTERNAL_SERVER_ERROR);
                out.print("{\"error\": \"Error executing Python prediction script.\", \"details\": \"" + scriptOutput.replace("\"", "'") + "\"}");
            }
            out.flush();

        } catch (Exception e) {
            response.setStatus(HttpServletResponse.SC_INTERNAL_SERVER_ERROR);
            response.getWriter().print("{\"error\": \"Server exception: " + e.getMessage().replace("\"", "'") + "\"}");
        }
    }
}
