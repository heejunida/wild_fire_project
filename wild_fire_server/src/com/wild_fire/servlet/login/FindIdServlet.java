package com.wild_fire.servlet.login;

import com.wild_fire.DAO.UserDAO;

import javax.servlet.http.*;
import javax.servlet.annotation.*;
import java.io.IOException;

@WebServlet("/findId")
public class FindIdServlet extends HttpServlet {
    protected void doPost(HttpServletRequest req, HttpServletResponse resp) throws IOException {
        req.setCharacterEncoding("UTF-8");
        String userName = req.getParameter("user_name");

        UserDAO dao = new UserDAO();
        String userId = dao.findUserIdByName(userName);

        resp.setContentType("application/json; charset=UTF-8");
        if (userId != null) {
            resp.getWriter().write("{\"result\":\"success\", \"user_id\":\"" + userId + "\"}");
        } else {
            resp.getWriter().write("{\"result\":\"fail\"}");
        }
    }
}