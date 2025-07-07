import google.generativeai as genai
from dotenv import load_dotenv
import os

load_dotenv(dotenv_path=".env")
print("Loaded GEMINI_API_KEY:", os.getenv("GEMINI_API_KEY"))

from flask import Flask, request, jsonify, send_from_directory, render_template
from flask_cors import CORS
import requests
import base64
import json


app = Flask(__name__)
CORS(app)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
SEARCH_API_KEY = os.getenv("SEARCH_API_KEY")


print(GEMINI_API_KEY)
GEMINI_API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}"

def mock_google_search(query):
    """Simulates Google Search results for testing purposes."""
    print(f"Simulating web search for: {query}")
    if "b&g foods sustainability" in query.lower() or "b&g foods allergy" in query.lower():
        return [
            {"title": "B&G Foods Corporate Responsibility", "snippet": "B&G Foods focuses on sustainable practices, community engagement, and product quality. Recent initiatives include reducing water usage in manufacturing. No major controversies recently.", "url": "https://www.bgfoods.com/sustainability"},
            {"title": "B&G Foods Investor Relations", "snippet": "Annual report highlights ESG (Environmental, Social, Governance) efforts and goals.", "url": "https://www.bgfoods.com/investors"},
            {"title": "B&G Foods issues recall over undeclared allergen", "snippet": "A recent recall was issued for a specific product due to undeclared peanut residue. Company states it was an isolated incident.", "url": "https://www.news.com/bg-foods-allergy-recall"}
        ]
    elif "nestle sustainability" in query.lower() or "nestle allergy" in query.lower():
        return [
            {"title": "Nestlé Waters Faces New Lawsuit Over Plastic Pollution", "snippet": "Environmental groups file suit alleging misleading claims and significant plastic waste contribution. Community protests over water extraction rights.", "url": "https://www.example-news.com/nestle-plastic-lawsuit"},
            {"title": "Nestlé's Commitment to Sustainability", "snippet": "Official page detailing efforts in responsible sourcing, water stewardship, and climate action. Targets set for reducing emissions.", "url": "https://www.nestle.com/sustainability"},
            {"title": "Child Labor Allegations in Cocoa Supply Chain", "snippet": "Report resurfaces concerns about child labor in some parts of Nestlé's cocoa supply chain, despite ongoing efforts to combat it.", "url": "https://www.another-news.com/cocoa-labor"},
            {"title": "Nestlé improves allergen control in factories", "snippet": "Nestlé announces new investments in production lines and staff training to minimize cross-contamination risks for common allergens.", "url": "https://www.nestle.com/allergen-control"}
        ]
    elif "patagonia sustainability" in query.lower() or "patagonia allergy" in query.lower():
        return [
            {"title": "Patagonia: Our Responsible Company", "snippet": "Known for environmental activism, using recycled materials, and fair labor practices. 'Worn Wear' program encourages repair and reuse.", "url": "https://www.patagonia.com/responsibility"},
            {"title": "Patagonia's Environmental Grants Program", "snippet": "Supports grassroots environmental organizations globally. Committed to 1% for the Planet.", "url": "https://www.patagonia.com/grants"}
        ]
    elif "ferrero u.s.a." in query.lower(): 
        return [ 
            {
                "title": "Ferrero Group Sustainability Initiatives",
                "snippet": "Global confectionery company with strong commitments to sustainable sourcing (cocoa, hazelnut, palm oil), climate action (emissions, renewable energy, water), packaging circularity, and social initiatives (child labor prevention, community engagement). High traceability goals. Some past criticism regarding palm oil, but they show strong efforts to mitigate.",
                "url": "https://www.ferrero.com/sustainability"
            }
        ]
    elif "ferrero group" in query.lower():
        return [
            {
                "title": "Ferrero Group Sustainability Initiatives",
                "snippet": "Global confectionery company with strong commitments to sustainable sourcing (cocoa, hazelnut, palm oil), climate action (emissions, renewable energy, water), packaging circularity, and social initiatives (child labor prevention, community engagement). High traceability goals. Some past criticism regarding palm oil, but they show strong efforts to mitigate.",
                "url": "https://www.ferrero.com/sustainability"
            }
        ]
    elif "unilever sustainability" in query.lower() or "unilever allergy" in query.lower():
        return [
            {"title": "Unilever Sustainable Living Plan Successes", "snippet": "Highlights progress in reducing environmental footprint, improving health and well-being, and enhancing livelihoods. Focus on palm oil and plastic.", "url": "https://www.unilever.com/sustainable-living"},
            {"title": "Report: Unilever Palm Oil Sourcing Still Linked to Deforestation", "snippet": "Despite commitments, an investigative report suggests ongoing challenges in achieving fully deforestation-free palm oil supply chains.", "url": "https://www.news-site.com/unilever-palm-oil"},
            {"title": "Unilever implements new allergen labeling standards", "snippet": "New, clearer labeling guidelines for all products containing the top 8 allergens to improve consumer safety.", "url": "https://www.unilever.com/allergy-info"}
        ]
    return []

COMPANY_SUSTAINABILITY_DATA = {
    "b&g foods": { "initial_score_impact": -10, "notes": "Large food conglomerate, diverse product range. Sustainability efforts may vary by brand." },
    "nestle": { "initial_score_impact": -20, "notes": "Global food and beverage giant. Known for significant environmental and social challenges." },
    "patagonia provisions": { "initial_score_impact": 15, "notes": "Known for strong environmental and ethical practices, recycled materials, fair labor." },
    "unilever": { "initial_score_impact": -5, "notes": "Large consumer goods company with varying sustainability initiatives across brands." }
}

# Values are points: positive for sustainable, negative for unsustainable
SUSTAINABILITY_SCORE_RULES = {
    "materials": {
        "organic cotton": 15, "recycled polyester": 10, "hemp": 12, "linen": 10, "tencel": 8, "lyocell": 8,
        "conventional cotton": -2, "polyester": -5, "nylon": -5, "acrylic": -5, "rayon": -3, "viscose": -3,
        "plastic": -5, "pvc": -10, "styrofoam": -10,
        "glass": 5, "aluminum": 5, "paper": 3, "cardboard": 3,
        "metal": 2, "wood": 3, "reclaimed wood": 10
    },
    "ingredients": {
        "high-fructose corn syrup": -5, "artificial flavors": -3, "no artificial flavors": 6, "artificial colors": -3,
        "no artificial colors": 6, "organic": 10, "natural flavors": 1, "real fruit": 5, "palm oil": -10, "non-gmo": 5,
        "soy lecithin": -8, "soy": -8, "high in protein": 3, "sugar": -5, "natural flavor": 2,
        "cocoa": -10, "chocolate": -8, "cocoa butter": -8, "chocolate liquor": -8, "red 40": -15, "toxic": -15, "whole grain oats":10
    },
    "certifications": {
        "fair trade": 15, "gots certified": 20, "bluesign": 18, "oeko-tex": 15, "usda organic": 15,
        "rainforest alliance certified": 10, "b corp": 20, "fda": 10
    },
    "claims": {
        "recycled content": 8, "biodegradable": 7, "compostable": 10, "sustainable source": 5,
        "eco-friendly": 2, "plant-based": 5, "vegan": 3, "cruelty-free": 3
    },
    "web_allegations": {
        "water usage controversy": -15, "plastic pollution lawsuit": -20, "deforestation link": -15,
        "child labor": -25, "environmental fine": -10, "greenwashing allegation": -10,
        "human rights violation": -20, "toxic waste": -20, "mass carbon emission": -10,
        "past criticism": -15
    },
    "web_positives": {
        "carbon neutral goal": 10, "renewable energy target": 3, "waste reduction initiative": 7,
        "circular economy program": 10, "community engagement": 5, "sustainable sourcing program": 10,
        "water stewardship": 8, "environmental activism": 15, "renewable energy": 10, 
    },
    "allergen_rules": {
        "recall": -20, "undeclared allergen": -15, "cross-contamination issue": -10,
        "allergen control": 10, "allergen labeling": 10, "dedicated facility": 15
    }
}

# Common allergens for detection
COMMON_ALLERGENS = ["milk", "eggs", "peanuts", "tree nuts", "soy", "wheat", "fish", "shellfish", "sesame", "Hazelnuts", "Gluten", "Lactose", "Dairy"]


PRODUCT_ALTERNATIVES = {
    "syrup": [
        {"name": "Local Organic Maple Syrup (Glass Bottle)", "reason": "Sustainably harvested, less processing, reusable packaging."},
        {"name": "Agave Nectar (Fair Trade Certified)", "reason": "Ethically sourced, good alternative if you want a different taste."}
    ],
    "clothing": [
        {"name": "Organic Cotton T-Shirt", "reason": "Uses less water and no harmful pesticides."},
        {"name": "Hemp or Linen Shirt", "reason": "Durable, requires less water and pesticides, highly renewable."},
        {"name": "Recycled Polyester Jacket", "reason": "Reduces plastic waste, but still sheds microplastics."}
    ],
    "plastic bottle": [
        {"name": "Reusable Stainless Steel Bottle", "reason": "Eliminates single-use plastic."},
        {"name": "Glass Container", "reason": "Easily recyclable, doesn't leach chemicals."},
    ]
}

async def search_and_analyze_company_sustainability(company_name):
    """
    Searches the web for sustainability claims/allegations for a given company
     and uses Gemini to summarize them.
    This function simulates an asynchronous operation.
    """
    if not company_name or company_name == "n/a":
        return {"allegations_from_web": [], "positives_from_web": [], "web_summary": "Company name not available for web search."}

    search_query = f"{company_name} sustainability allegations OR initiatives OR environmental controversies OR allergy issues OR recall OR allergen control"
    search_results = mock_google_search(search_query)

    if not search_results:
        return {"allegations_from_web": [], "positives_from_web": [], "web_summary": "No relevant web search results found for the company's sustainability."}

    context_for_gemini = "Web Search Results:\n\n"
    for i, result in enumerate(search_results[:5]):
        context_for_gemini += f"Result {i+1} (Title: {result.get('title', 'N/A')}, URL: {result.get('url', 'N/A')}):\n"
        context_for_gemini += f"Snippet: {result.get('snippet', 'N/A')}\n\n"

    # Prompt Gemini to summarize sustainability and allergy claims/allegations
    prompt_for_gemini = f"""
    Based on the following web search results about "{company_name}", identify and list:
    1.  Specific allegations or controversies related to their environmental, social, or ethical practices.
    2.  Specific positive initiatives or commitments related to their sustainability efforts.
    3.  **Any reported allergy-related issues, recalls, or positive allergen control measures.**
    
    Return the information as a JSON object, without any additional text or markdown outside the JSON block.

    {{
      "allegations_from_web": [],
      "positives_from_web": [],
      "allergy_issues_from_web": [], # New field for allergy-related findings
      "web_summary": ""
    }}
    
    Context:
    {context_for_gemini}
    """
    
    payload = {
        "contents": [
            {
                "role": "user",
                "parts": [
                    {"text": prompt_for_gemini}
                ]
            }
        ],
        "generationConfig": {
            "responseMimeType": "application/json"
        }
    }

    try:
        gemini_response = requests.post(GEMINI_API_URL, json=payload)
        gemini_response.raise_for_status()
        gemini_result = gemini_response.json()

        gemini_text_part = ""
        if gemini_result.get("candidates") and gemini_result["candidates"][0].get("content") and gemini_result["candidates"][0]["content"].get("parts"):
            gemini_text_part = gemini_result["candidates"][0]["content"]["parts"][0]["text"]
        
        if gemini_text_part.startswith("```json") and gemini_text_part.endswith("```"):
            gemini_text_part = gemini_text_part[len("```json"):-len("```")].strip()
        
        parsed_web_analysis = json.loads(gemini_text_part)
        return parsed_web_analysis

    except requests.exceptions.RequestException as e:
        print(f"Error calling Gemini for web analysis: {e}")
        return {"allegations_from_web": [], "positives_from_web": [], "allergy_issues_from_web": [], "web_summary": f"Failed to analyze web data: {e}"}
    except json.JSONDecodeError as e:
        print(f"JSON decode error from Gemini web analysis: {e}")
        return {"allegations_from_web": [], "positives_from_web": [], "allergy_issues_from_web": [], "web_summary": f"Failed to parse AI web analysis: {e}. Raw: {gemini_text_part[:100]}..."}
    except Exception as e:
        print(f"An unexpected error occurred during web analysis: {e}")
        return {"allegations_from_web": [], "positives_from_web": [], "allergy_issues_from_web": [], "web_summary": f"An unexpected error occurred during web analysis: {e}"}


def analyze_sustainability(gemini_data, company_web_analysis):
    """
    Performs a more comprehensive sustainability analysis based on Gemini's extracted data
    AND web search analysis. Assigns a score and collects relevant information.
    """
    score = 80
    summary_messages = []
    allergy_info = {
        "identified_allergens": [],
        "company_allergy_notes": [],
        "product_allergy_summary": "No common allergens identified or specific allergy issues found."
    }
    
    product_name = gemini_data.get("product_name", "N/A")
    company_name_raw = gemini_data.get("company_name", "").lower()
    product_type = gemini_data.get("product_type", "general product")
    
    summary_messages.append(f"🔍 Company: {company_name_raw.title()}")
    company_info = COMPANY_SUSTAINABILITY_DATA.get(company_name_raw.replace(" ", ""), None)

    if company_info:
        score += company_info["initial_score_impact"]
        summary_messages.append(f"Company Base Notes: {company_info['notes']}")
    else:
        summary_messages.append(f"Company: {company_name_raw.title()} (Base sustainability data not readily available in our simplified database).")

    if company_web_analysis and company_web_analysis.get("allegations_from_web"):
        summary_messages.append("⚠️ **Company Environmental/Social Allegations (from Web Search):**")
        for allegation in company_web_analysis["allegations_from_web"]:
            score_change = 0
            found_negative_keyword = False
            for keyword, pts in SUSTAINABILITY_SCORE_RULES["web_allegations"].items():
                if keyword in allegation.lower():
                    score_change = pts
                    score += pts
                    found_negative_keyword = True
                    break
            summary_messages.append(f"- {allegation} (Score adjusted by {score_change} points)")
            if not found_negative_keyword:
                score -= 5
                summary_messages.append(f"- {allegation} (Default minor penalty applied)")
                
    if company_web_analysis and company_web_analysis.get("positives_from_web"):
        summary_messages.append("✅ **Company Positive Initiatives (from Web Search):**")
        for positive in company_web_analysis["positives_from_web"]:
            score_change = 0
            found_positive_keyword = False
            for keyword, pts in SUSTAINABILITY_SCORE_RULES["web_positives"].items():
                if keyword in positive.lower():
                    score_change = pts
                    score += pts
                    found_positive_keyword = True
                    break
            summary_messages.append(f"- {positive} (Score adjusted by +{score_change} points)")
            if not found_positive_keyword:
                score += 3
                summary_messages.append(f"- {positive} (Default minor bonus applied)")

    if company_web_analysis and company_web_analysis.get("web_summary"):
        summary_messages.append(f"\nWeb Reputation Summary: {company_web_analysis['web_summary']}")

    summary_messages.append(f"\n📊 Product Sustainability Breakdown:")

    product_has_allergens = False
    allergy_messages = []

    if gemini_data.get("ingredients_or_materials") and product_type.lower() == 'food':
        found_product_allergens = []
        for item in gemini_data["ingredients_or_materials"]:
            item_lower = item.lower()
            for allergen in COMMON_ALLERGENS:
                if allergen in item_lower:
                    found_product_allergens.append(allergen.title())
                    product_has_allergens = True
        
        if found_product_allergens:
            allergy_messages.append(f"Contains common allergens: {', '.join(set(found_product_allergens))}.")
            allergy_info["identified_allergens"] = list(set(found_product_allergens))
        
    if company_web_analysis and company_web_analysis.get("allergy_issues_from_web"):
        company_has_allergy_issues = False
        for issue in company_web_analysis["allergy_issues_from_web"]:
            issue_lower = issue.lower()
            allergy_info["company_allergy_notes"].append(issue)
            
            found_allergen_rule = False
            for keyword, pts in SUSTAINABILITY_SCORE_RULES["allergen_rules"].items():
                if keyword in issue_lower:
                    score += pts
                    summary_messages.append(f"- Company allergy note: {issue} (Score adjusted by {pts} points).")
                    company_has_allergy_issues = True
                    found_allergen_rule = True
                    break
            if not found_allergen_rule:
                score -= 5
                summary_messages.append(f"- Company allergy note: {issue} (Default minor penalty applied).")
                company_has_allergy_issues = True

        if company_has_allergy_issues:
            allergy_messages.append("Company has reported allergy-related issues or recalls from web search.")
        else:
            allergy_messages.append("No specific allergy-related issues found for the company via web search.")
    
    if product_has_allergens or (company_web_analysis and company_web_analysis.get("allergy_issues_from_web")):
        allergy_info["product_allergy_summary"] = " ".join(allergy_messages)
    
    summary_messages.append(f"\n🚨 **Allergy Information:**")
    summary_messages.append(allergy_info["product_allergy_summary"])
    if allergy_info["identified_allergens"]:
        summary_messages.append(f"Product contains: {', '.join(allergy_info['identified_allergens'])}.")
    if allergy_info["company_allergy_notes"]:
        summary_messages.append(f"Company allergy-related web findings: {'; '.join(allergy_info['company_allergy_notes'])}.")

    if gemini_data.get("ingredients_or_materials"):
        summary_messages.append("\nMaterials/Ingredients Identified:")
        for item in gemini_data["ingredients_or_materials"]:
            item_lower = item.lower()
            found_score_for_item = False

            for material, pts in SUSTAINABILITY_SCORE_RULES["materials"].items():
                if material in item_lower:
                    score += pts
                    summary_messages.append(f"- {item.title()}: Score adjustment by {pts} points (Material/Packaging).")
                    found_score_for_item = True
                    break

            if not found_score_for_item:
                for ingredient, pts in SUSTAINABILITY_SCORE_RULES["ingredients"].items():
                    if ingredient in item_lower:
                        score += pts
                        summary_messages.append(f"- {item.title()}: Score adjustment by {pts} points (Ingredient).")
                        found_score_for_item = True
                        break
            
            if not found_score_for_item:
                summary_messages.append(f"- {item.title()} (no specific sustainability rule found, neutral impact assumed).")
    else:
        summary_messages.append("- No explicit materials or ingredients listed by AI from label.")

    if gemini_data.get("certifications_or_eco_labels"):
        summary_messages.append("\nCertifications/Eco-Labels Identified from Label:")
        found_certifications = False
        for cert in gemini_data["certifications_or_eco_labels"]:
            cert_lower = cert.lower()
            found_score = False
            for known_cert, pts in SUSTAINABILITY_SCORE_RULES["certifications"].items():
                if known_cert in cert_lower:
                    score += pts
                    summary_messages.append(f"- {cert.title()}: Positive impact (+{pts} points).")
                    found_score = True
                    found_certifications = True
                    break
            if not found_score:
                summary_messages.append(f"- {cert.title()} (not in our known certification list, neutral impact assumed).")
        if not found_certifications:
            summary_messages.append("- No known sustainability certifications recognized from label.")
    else:
        summary_messages.append("- No certifications or eco-labels detected from label.")

    if gemini_data.get("sustainability_claims_on_label"):
        summary_messages.append("\nSustainability Claims Identified on Label:")
        found_claims = False
        for claim in gemini_data["sustainability_claims_on_label"]:
            claim_lower = claim.lower()
            found_score = False
            for known_claim, pts in SUSTAINABILITY_SCORE_RULES["claims"].items():
                if known_claim in claim_lower:
                    score += pts
                    summary_messages.append(f"- {claim.title()}: Positive impact (+{pts} points for this claim).")
                    found_score = True
                    found_claims = True
                    break
            if not found_score:
                summary_messages.append(f"- {claim.title()} (claim identified, but no specific rule found).")
        if not found_claims:
            summary_messages.append("- No specific sustainability claims recognized on label.")
    else:
        summary_messages.append("- No sustainability claims detected on the label.")

    score = max(0, min(100, score))

    overall_rating = ""
    if score >= 80:
        overall_rating = "Excellent! ✨"
    elif score >= 60:
        overall_rating = "Good. 🌱"
    elif score >= 40:
        overall_rating = "Moderate. 💡"
    else:
        overall_rating = "Needs Improvement. 📉"

    summary_messages.append(f"\n--- Overall Sustainability Score: **{score}/100** ({overall_rating}) ---")

    alternatives = []
    if product_type and product_type.lower() in PRODUCT_ALTERNATIVES:
        alternatives.extend(PRODUCT_ALTERNATIVES[product_type.lower()])
    elif product_name and product_name.lower() in PRODUCT_ALTERNATIVES:
        alternatives.extend(PRODUCT_ALTERNATIVES[product_name.lower()])
    
    if not alternatives:
        alternatives.append({"name": "Research specific eco-friendly brands", "reason": "Look for companies focused on sustainability in your product's category."})

    return {
        "score": score,
        "summary": "\n".join(summary_messages),
        "alternatives": alternatives,
        "allergy_info": allergy_info
    }

@app.route('/')
def serve_index():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
async def analyze_product():
    if 'image' not in request.files:
        return jsonify({"error": "No image file provided"}), 400
    file = request.files['image']
    if not file:
        return jsonify({"error": "Empty image file"}), 400

    gemini_text_part = ""

    try:
        image_data = file.read()
        base64_image = base64.b64encode(image_data).decode('utf-8')
        mime_type = file.mimetype

        prompt_label_analysis = """
        You are an expert in product and textile label sustainability and allergy analysis.
        Analyze the image of a product label, packaging, or clothing tag.
        Extract the following information and output it as a JSON object.

        {
          "product_name": "",
          "company_name": "",
          "product_type": "",
          "ingredients_or_materials": [],
          "certifications_or_eco_labels": [],
          "sustainability_claims_on_label": [],
          "visible_recycling_info": "",
          "country_of_origin": "",
          "additional_notes": ""
        }

        If a piece of information is not found, use an empty string for strings or an empty array for lists.
        Focus on extracting exact ingredients for allergy analysis.
        """

        payload_label_analysis = {
            "contents": [
                {
                    "role": "user",
                    "parts": [
                        {"text": prompt_label_analysis},
                        {"inlineData": {"mimeType": mime_type, "data": base64_image}}
                    ]
                }
            ],
            "generationConfig": {
                "responseMimeType": "application/json"
            }
        }

        gemini_response_label = requests.post(GEMINI_API_URL, json=payload_label_analysis)
        gemini_response_label.raise_for_status()

        gemini_result_label = gemini_response_label.json()
        
        if gemini_result_label.get("candidates") and gemini_result_label["candidates"][0].get("content") and gemini_result_label["candidates"][0]["content"].get("parts"):
            gemini_text_part = gemini_result_label["candidates"][0]["content"]["parts"][0]["text"]
        
        if gemini_text_part.startswith("```json") and gemini_text_part.endswith("```"):
            gemini_text_part = gemini_text_part[len("```json"):-len("```")].strip()
        
        gemini_parsed_data = json.loads(gemini_text_part)

        company_name_for_search = gemini_parsed_data.get("company_name", "").strip()

        company_web_analysis_results = {}
        if company_name_for_search:
            company_web_analysis_results = await search_and_analyze_company_sustainability(company_name_for_search)
        else:
            company_web_analysis_results["web_summary"] = "No company name found on label for web search."

        sustainability_analysis_results = analyze_sustainability(gemini_parsed_data, company_web_analysis_results)

        return jsonify({
            "success": True,
            "gemini_raw_output_label": gemini_text_part,
            "gemini_parsed_data": gemini_parsed_data,
            "company_web_analysis": company_web_analysis_results,
            "sustainability_score": sustainability_analysis_results["score"],
            "sustainability_summary": sustainability_analysis_results["summary"],
            "product_alternatives": sustainability_analysis_results["alternatives"],
            "allergy_info": sustainability_analysis_results["allergy_info"]
        })

    except requests.exceptions.RequestException as e:
        print(f"Request error: {e}")
        return jsonify({"error": f"Failed to connect to AI service or external resource: {e}"}), 500
    except json.JSONDecodeError as e:
        print(f"JSON decode error: {e}")
        print(f"Gemini raw output: {gemini_text_part}")
        return jsonify({"error": f"Failed to parse AI response (JSON error): {e}. Raw response: {gemini_text_part[:200]}..."}), 500
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return jsonify({"error": f"An unexpected error occurred: {e}"}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
